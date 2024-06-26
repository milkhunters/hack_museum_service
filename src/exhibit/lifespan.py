import asyncio
import json
import logging
import os
from typing import Callable

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from exhibit.config import Config, ImgSearcherConfig
from exhibit.db import create_psql_async_session
from exhibit.services.auth.scheduler import update_reauth_list
from exhibit.services.img_searcher import ImgSearchAdapter, update_task_result
from exhibit.utils.s3 import S3Storage


async def init_db(app: FastAPI, config: Config):
    engine, session = create_psql_async_session(
        host=config.DB.POSTGRESQL.HOST,
        port=config.DB.POSTGRESQL.PORT,
        username=config.DB.POSTGRESQL.USERNAME,
        password=config.DB.POSTGRESQL.PASSWORD,
        database=config.DB.POSTGRESQL.DATABASE,
        echo=config.DEBUG,
    )
    app.state.db_session = session


async def init_reauth_checker(app: FastAPI, config: Config):
    scheduler = AsyncIOScheduler()
    ums_grps_host = os.getenv("UMS_GRPC_HOST")
    ums_grps_port = int(os.getenv("UMS_GRPC_PORT"))
    scheduler.add_job(
        update_reauth_list,
        'interval',
        seconds=5,
        args=[app, config, (ums_grps_host, ums_grps_port)]
    )
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    scheduler.start()


async def init_img_search_adapter(app: FastAPI, config: ImgSearcherConfig):
    async def get_connection() -> AbstractRobustConnection:
        return await aio_pika.connect_robust(
            host=config.RABBITMQ.HOST,
            port=config.RABBITMQ.PORT,
            login=config.RABBITMQ.USERNAME,
            password=config.RABBITMQ.PASSWORD,
            virtualhost=config.RABBITMQ.VHOST,
        )

    connection_pool = Pool(get_connection, max_size=2)

    async def get_channel() -> aio_pika.Channel:
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    channel_pool = Pool(get_channel, max_size=10)

    getattr(app, "state").task_result = dict()

    getattr(app, "state").isa = ImgSearchAdapter(
        channel_pool,
        config
    )

    async def consume() -> None:
        async with channel_pool.acquire() as channel:
            queue = await channel.declare_queue(
                config.SEARCHER_TASKS_RECEIVER_ID,
                durable=True,
                exclusive=False,
            )
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await message.ack()
                    await update_task_result(message, app)

    async with connection_pool, channel_pool:
        await consume()


async def init_s3_storage(app: FastAPI, config: Config):
    app.state.file_storage = await S3Storage(
        bucket=config.DB.S3.BUCKET,
        external_host=config.DB.S3.PUBLIC_ENDPOINT_URL
    ).create_session(
        endpoint_url=config.DB.S3.ENDPOINT_URL,
        region_name=config.DB.S3.REGION,
        access_key_id=config.DB.S3.ACCESS_KEY_ID,
        secret_access_key=config.DB.S3.ACCESS_KEY,
    )


def create_start_app_handler(app: FastAPI, config: Config) -> Callable:
    async def start_app() -> None:
        logging.debug("Выполнение FastAPI startup event handler.")
        await init_db(app, config)
        await init_s3_storage(app, config)

        app.state.reauth_session_dict = dict()
        await init_reauth_checker(app, config)

        asyncio.get_running_loop().create_task(
            init_img_search_adapter(app, config.IMG_SEARCHER)
        )

        logging.info("FastAPI Успешно запущен.")

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        logging.debug("Выполнение FastAPI shutdown event handler.")

    return stop_app
