import json
import uuid
from typing import Literal

from exhibit import exceptions
from exhibit.models import schemas
from exhibit.models.permission import Permission
from exhibit.models.auth import BaseUser
from exhibit.models.state import ExhibitState, UserState, RateState
from exhibit.services import ImgSearchAdapter
from exhibit.services.auth.filters import state_filter
from exhibit.services.auth.filters import permission_filter
from exhibit.services.repository import CommentTreeRepo, LikeRepo, FileRepo
from exhibit.services.repository import CommentRepo
from exhibit.services.repository import ExhibitRepo
from exhibit.services.repository import TagRepo
from exhibit.utils.s3 import S3Storage


class ExhibitApplicationService:

    def __init__(
            self,
            current_user: BaseUser,
            exhibit_repo: ExhibitRepo,
            tag_repo: TagRepo,
            comment_tree_repo: CommentTreeRepo,
            comment_repo: CommentRepo,
            like_repo: LikeRepo,
            file_repo: FileRepo,
            file_storage: S3Storage,
            isa: ImgSearchAdapter

    ):
        self._current_user = current_user
        self._repo = exhibit_repo
        self._tag_repo = tag_repo
        self._tree_repo = comment_tree_repo
        self._comment_repo = comment_repo
        self._like_repo = like_repo
        self._file_repo = file_repo
        self._file_storage = file_storage
        self._isa = isa

    async def get_exhibits(
            self,
            page: int = 1,
            per_page: int = 10,
            order_by: Literal["title", "updated_at", "created_at"] = "created_at",
            query: str = None,
            state: ExhibitState = ExhibitState.PUBLISHED,
            owner_id: uuid.UUID = None
    ) -> list[schemas.ExhibitSmall]:
        """
        Получить список экспонатов

        :param page: номер страницы (всегда >= 1)
        :param per_page: количество экспонатов на странице (всегда >= 1, но <= per_page_limit)
        :param order_by: поле сортировки
        :param query: поисковый запрос (если необходим)
        :param state: статус экспоната (по умолчанию только опубликованные)
        :param owner_id: id владельца экспоната (если необходимо получить экспоната только одного пользователя)
        :return:

        """

        if page < 1:
            raise exceptions.NotFound("Страница не найдена")
        if per_page < 1:
            raise exceptions.BadRequest("Неверное количество элементов на странице")

        if all(
                (
                        state != ExhibitState.PUBLISHED,
                        owner_id != self._current_user.id,
                        Permission.GET_PRIVATE_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете получить список приватных экспонатов")

        if all(
                (
                        state != ExhibitState.PUBLISHED,
                        owner_id == self._current_user.id,
                        Permission.GET_SELF_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете получить свой список приватных экспонатов")

        if all(
                (
                        state == ExhibitState.PUBLISHED,
                        Permission.GET_PUBLIC_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете получить список опубликованных экспонатов")

        per_page_limit = 40

        # Подготовка входных данных
        per_page = min(per_page, per_page_limit, 2147483646)
        offset = min((page - 1) * per_page, 2147483646)

        # Выполнение запроса
        if query:
            exhibits = await self._repo.search(
                query=query,
                fields=["title", "content"],
                limit=per_page,
                offset=offset,
                order_by=order_by,
                **{"state": state} if state else {},
                **{"owner_id": owner_id} if owner_id else {}
            )
        else:
            exhibits = await self._repo.get_all(
                limit=per_page,
                offset=offset,
                order_by=order_by,
                **{"state": state} if state else {},
                **{"owner_id": owner_id} if owner_id else {}
            )
        return [schemas.ExhibitSmall.model_validate(exhibit) for exhibit in exhibits]

    async def get_exhibit(self, exhibit_id: uuid.UUID) -> schemas.Exhibit:
        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if all(
                (
                        exhibit.state != ExhibitState.PUBLISHED,
                        exhibit.owner_id != self._current_user.id,
                        Permission.GET_PRIVATE_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Материал не опубликован")

        if all(
                (
                        exhibit.state != ExhibitState.PUBLISHED,
                        exhibit.owner_id == self._current_user.id,
                        Permission.GET_SELF_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать свои приватные публикации")

        if all(
                (
                        exhibit.state == ExhibitState.PUBLISHED,
                        Permission.GET_PUBLIC_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать публичные публикации")

        # Views
        if exhibit.state == ExhibitState.PUBLISHED and exhibit.owner_id != self._current_user.id:
            exhibit.views += 1
            await self._repo.session.commit()
            await self._repo.session.refresh(exhibit)

        # Likes
        exhibit.likes_count = await self._like_repo.count(exhibit_id=exhibit_id)

        return schemas.Exhibit.model_validate(exhibit)

    @permission_filter(Permission.CREATE_SELF_EXHIBITS)
    @state_filter(UserState.ACTIVE)
    async def create_exhibit(self, data: schemas.ExhibitCreate) -> schemas.Exhibit:
        _ = await self._repo.create(
            **data.model_dump(exclude_unset=True, exclude={"tags"}),
            owner_id=self._current_user.id
        )
        exhibit = await self._repo.get(id=_.id)
        exhibit.likes_count = 0
        # Добавление тегов
        for tag_title in data.tags:
            tag = await self._tag_repo.get(title=tag_title)
            if not tag:
                tag = await self._tag_repo.create(title=tag_title)
            exhibit.tags.append(tag)
        await self._repo.session.commit()
        return schemas.Exhibit.model_validate(exhibit)

    @state_filter(UserState.ACTIVE)
    async def update_exhibit(self, exhibit_id: uuid.UUID, data: schemas.ExhibitUpdate) -> None:
        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if (
                exhibit.owner_id != self._current_user.id and
                Permission.UPDATE_USER_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не являетесь владельцем экспоната")

        if (
                exhibit.owner_id == self._current_user.id and
                Permission.UPDATE_SELF_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не можете редактировать свои экспоната")

        if data.tags:
            exhibit.tags = []
            for tag_title in data.tags:
                tag = await self._tag_repo.get(title=tag_title)
                if not tag:
                    tag = await self._tag_repo.create(title=tag_title)
                exhibit.tags.append(tag)
            await self._repo.session.commit()

        await self._repo.update(exhibit_id, **data.model_dump(exclude_unset=True, exclude={"tags"}))

    @permission_filter(Permission.RATE_EXHIBITS)
    @state_filter(UserState.ACTIVE)
    async def rate_exhibit(self, exhibit_id: uuid.UUID, state: RateState) -> None:
        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if exhibit.owner_id == self._current_user.id:
            raise exceptions.BadRequest("Вы не можете оценивать свои экспоната")

        like = await self._like_repo.get(exhibit_id=exhibit_id, owner_id=self._current_user.id)
        if state == RateState.LIKE:
            if like:
                raise exceptions.BadRequest("Вы уже поставили лайк")
            await self._like_repo.create(exhibit_id=exhibit_id, owner_id=self._current_user.id)
        elif state == RateState.NEUTRAL:
            if not like:
                raise exceptions.BadRequest("Вы еще не оценили статью")
            await self._like_repo.delete(like.id)

    @state_filter(UserState.ACTIVE)
    async def delete_exhibit(self, exhibit_id: uuid.UUID) -> None:
        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if (
                exhibit.owner_id != self._current_user.id and
                Permission.DELETE_USER_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не являетесь владельцем экспоната")

        if (
                exhibit.owner_id == self._current_user.id and
                Permission.DELETE_SELF_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не можете удалять свои экспоната")

        await self._repo.delete(id=exhibit_id)
        await self._comment_repo.delete_comments_by_exhibit(exhibit_id)

    async def get_exhibit_files(self, exhibit_id: uuid.UUID) -> list[schemas.ExhibitFileItem]:
        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if all(
                (
                        exhibit.state != ExhibitState.PUBLISHED,
                        exhibit.owner_id != self._current_user.id,
                        Permission.GET_PRIVATE_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать файлы неопубликованных экспонатов")

        if all(
                (
                        exhibit.state != ExhibitState.PUBLISHED,
                        exhibit.owner_id == self._current_user.id,
                        Permission.GET_SELF_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать файлы своих приватных публикаций")

        if all(
                (
                        exhibit.state == ExhibitState.PUBLISHED,
                        Permission.GET_PUBLIC_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать файлы публичных публикаций")

        resp = []

        files = await self._file_repo.get_all(exhibit_id=exhibit_id, is_uploaded=True)

        for file in files:
            url = self._file_storage.generate_download_public_url(
                file_path=f"{exhibit.id}/{file.id}",
                content_type=file.content_type,
                rcd="inline",
                filename=file.filename
            )
            resp.append(schemas.ExhibitFileItem(
                url=url,
                **schemas.ExhibitFile.model_validate(file).model_dump(exclude={"is_uploaded", "exhibit_id"})
            ))

        return resp

    async def get_exhibit_file(
            self,
            exhibit_id: uuid.UUID,
            file_id: uuid.UUID,
            download: bool
    ) -> schemas.ExhibitFileItem:

        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if all(
                (
                        exhibit.state != ExhibitState.PUBLISHED,
                        exhibit.owner_id != self._current_user.id,
                        Permission.GET_PRIVATE_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать файлы неопубликованных экспонатов")

        if all(
                (
                        exhibit.state != ExhibitState.PUBLISHED,
                        exhibit.owner_id == self._current_user.id,
                        Permission.GET_SELF_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать файлы своих приватных публикаций")

        if all(
                (
                        exhibit.state == ExhibitState.PUBLISHED,
                        Permission.GET_PUBLIC_EXHIBITS.value not in self._current_user.permissions
                )
        ):
            raise exceptions.AccessDenied("Вы не можете просматривать файлы публичных публикаций")

        file = await self._file_repo.get(id=file_id)
        if not file:
            raise exceptions.NotFound("Файл не найден")

        if not file.is_uploaded:
            raise exceptions.NotFound("Файл не загружен")

        url = self._file_storage.generate_download_public_url(
            file_path=f"{exhibit.id}/{file.id}",
            content_type=file.content_type,
            rcd="attachment" if download else "inline",
            filename=file.filename
        )

        return schemas.ExhibitFileItem(
            url=url,
            **schemas.ExhibitFile.model_validate(file).model_dump(exclude={"is_uploaded", "exhibit_id"})
        )

    @state_filter(UserState.ACTIVE)
    async def upload_exhibit_file(
            self,
            exhibit_id: uuid.UUID,
            data: schemas.FileCreate
    ) -> schemas.FileUpload:

        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if exhibit.state == ExhibitState.DELETED:
            raise exceptions.BadRequest("Вы не можете загружать файлы для экспонатов, которые были удалены")

        if (
                exhibit.owner_id != self._current_user.id and
                Permission.UPDATE_USER_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не являетесь владельцем экспоната")

        if (
                exhibit.owner_id == self._current_user.id and
                Permission.UPDATE_SELF_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не можете редактировать свои экспонаты")

        file = await self._file_repo.create(
            filename=data.filename,
            exhibit_id=exhibit_id,
            content_type=data.content_type.value
        )

        url = schemas.PreSignedPostUrl.model_validate(
            await self._file_storage.generate_upload_url(
                file_path=f"{exhibit.id}/{file.id}",
                content_type=data.content_type.value,
                content_length=(1, 100 * 1024 * 1024),  # 100mb
                expires_in=30 * 60  # 30 min
            )
        )

        return schemas.FileUpload(
            file_id=file.id,
            upload_url=url
        )

    @state_filter(UserState.ACTIVE)
    async def confirm_exhibit_file_upload(
            self,
            exhibit_id: uuid.UUID,
            file_id: uuid.UUID
    ) -> None:

        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найден")

        if exhibit.state == ExhibitState.DELETED:
            raise exceptions.BadRequest("Вы не можете подтверждать файлы для экспонатов, которые были удалены")

        if (
                exhibit.owner_id != self._current_user.id and
                Permission.UPDATE_USER_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не являетесь владельцем экспоната")

        if (
                exhibit.owner_id == self._current_user.id and
                Permission.UPDATE_SELF_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не можете подтверждать загрузку файлов")

        file = await self._file_repo.get(id=file_id)
        if not file:
            raise exceptions.NotFound("Файл не найден")

        if file.exhibit_id != exhibit_id:
            raise exceptions.BadRequest("Файл не принадлежит экспонату")

        if file.is_uploaded:
            raise exceptions.BadRequest("Файл уже загружен")

        info = await self._file_storage.info(file_path=f"{exhibit_id}/{file_id}")
        if not info:
            raise exceptions.NotFound("Файл не загружен")

        await self._file_repo.update(id=file_id, is_uploaded=True)
        await self._repo.update(exhibit_id, poster=file_id)

        await self._isa.send_data(
            json.dumps({
                "file_id": str(file_id),
                "command": "add"
            }))

    @state_filter(UserState.ACTIVE)
    async def delete_exhibit_file(self, exhibit_id: uuid.UUID, file_id: uuid.UUID) -> None:
        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if exhibit.state == ExhibitState.DELETED:
            raise exceptions.BadRequest("Вы не можете удалять файлы экспонатов, которые были удалены")

        if (
                exhibit.owner_id != self._current_user.id and
                Permission.UPDATE_USER_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не являетесь владельцем экспоната")

        if (
                exhibit.owner_id == self._current_user.id and
                Permission.UPDATE_SELF_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не можете удалять файлы")

        file = await self._file_repo.get(id=file_id)
        if not file:
            raise exceptions.NotFound("Файл не найден")

        if file.exhibit_id != exhibit_id:
            raise exceptions.BadRequest("Файл не принадлежит экспонату")

        if not file.is_uploaded:
            raise exceptions.BadRequest("Файл не загружен")

        if exhibit.poster == file_id:
            await self._repo.update(id=exhibit_id, poster=None)

        await self._file_storage.delete(file_path=f"{exhibit_id}/{file_id}")
        await self._file_repo.delete(id=file_id)

    @state_filter(UserState.ACTIVE)
    async def set_exhibit_poster(self, exhibit_id: uuid.UUID, file_id: uuid.UUID) -> None:
        exhibit = await self._repo.get(id=exhibit_id)
        if not exhibit:
            raise exceptions.NotFound("Экспонат не найдена")

        if exhibit.state == ExhibitState.DELETED:
            raise exceptions.BadRequest("Вы не можете устанавливать постер для экспонатов, которые были удалены")

        if (
                exhibit.owner_id != self._current_user.id and
                Permission.UPDATE_USER_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не являетесь владельцем экспоната")

        if (
                exhibit.owner_id == self._current_user.id and
                Permission.UPDATE_SELF_EXHIBITS.value not in self._current_user.permissions
        ):
            raise exceptions.AccessDenied("Вы не можете установить постер для своих экспонатов")

        file = await self._file_repo.get(id=file_id)
        if not file:
            raise exceptions.NotFound("Файл не найден")

        if file.exhibit_id != exhibit_id:
            raise exceptions.BadRequest("Файл не принадлежит экспонату")

        if not file.is_uploaded:
            raise exceptions.BadRequest("Файл не загружен")

        if exhibit.poster == file_id:
            raise exceptions.BadRequest("Этот файл уже является постером экспоната")

        await self._repo.update(id=exhibit_id, poster=file_id)

        await self._isa.send_data(
            json.dumps({
                "file_id": str(file_id),
                "command": "add"
            }))
