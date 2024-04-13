import json
import logging
import uuid
from typing import Any

import aio_pika

from exhibit import exceptions
from exhibit.config import ImgSearcherConfig
from exhibit.models import schemas
from exhibit.models.auth import BaseUser
from exhibit.models.schemas import ExhibitSmall
from exhibit.services.repository import ExhibitRepo
from exhibit.utils.s3 import S3Storage


class ImgSearcherApplicationService:

    def __init__(
            self,
            current_user: BaseUser,
            exhibit_repo: ExhibitRepo,
            file_storage: S3Storage,
            isa: "ImgSearchAdapter",
            task_result: dict[str, Any]

    ):
        self._current_user = current_user
        self._repo = exhibit_repo
        self._file_storage = file_storage
        self._task_result = task_result
        self._isa = isa

    async def make_upload_url_file(
            self,
            data: schemas.FileCreate
    ) -> schemas.FileUpload:

        file_id = uuid.uuid4()

        url = schemas.PreSignedPostUrl.model_validate(
            await self._file_storage.generate_upload_url(
                file_path=f"searcher/{file_id}",
                content_type=data.content_type.value,
                content_length=(1, 100 * 1024 * 1024),  # 100mb
                expires_in=30 * 60  # 30 min
            )
        )

        return schemas.FileUpload(
            file_id=file_id,
            upload_url=url
        )

    async def make_search_task(
            self,
            file_id: uuid.UUID
    ):

        info = await self._file_storage.info(file_path=f"searcher/{file_id}")
        if not info:
            raise exceptions.NotFound("Файл не загружен")

        if self._task_result.get(str(file_id)):
            raise exceptions.ConflictError("Задание уже выполнено или выполняется")

        body = {
            "file_id": str(file_id),
            "command": "search"
        }

        await self._isa.send_data(
            json.dumps(body)
        )

        self._task_result[str(file_id)] = dict(
            status="in_process",
            result=[]
        )

    async def get_task_result(
            self,
            file_id: uuid.UUID
    ) -> list[ExhibitSmall]:

        data = self._task_result.get(str(file_id))
        if data is None:
            raise exceptions.NotFound("Задачи не существует")

        if data["status"] == "in_process":
            raise exceptions.APIError("Задача находится в процессе выполнения", status_code=202)

        if not data["result"]:
            return []

        result = await self._repo.get_exhibits_by_ids(data["result"])
        return [ExhibitSmall.model_validate(exhibit) for exhibit in result]


class ImgSearchAdapter:
    def __init__(self, rmq: aio_pika.abc.AbstractRobustConnection, config: ImgSearcherConfig):
        self._rmq = rmq
        self._config = config

    async def send_data(
            self,
            body: str

    ):
        channel = await self._rmq.channel()

        await channel.declare_queue(
            self._config.SEARCHER_TASKS_SENDER_ID,
            durable=True,
            exclusive=False,
            auto_delete=False
        )

        await channel.default_exchange.publish(
            aio_pika.Message(body=body.encode()),
            routing_key=self._config.SEARCHER_TASKS_SENDER_ID
        )


async def update_task_result(
        message: aio_pika.IncomingMessage,
        app
):
    await message.ack()

    message_body = message.body.decode()
    logging.debug(f"[RMQ ImgSearch] Received message")

    result = json.loads(message_body)

    file_id = result.get("file_id")
    if not file_id:
        logging.warning("[RMQ ImgSearch] Task id not found in result")
        return

    content = result.get("result")
    if content is None:
        logging.warning("[RMQ ImgSearch] Result list not found in result")
        return

    app.state.task_result[file_id] = dict(
        status="done",
        result=[uuid.UUID(_) for _ in content]
    )


