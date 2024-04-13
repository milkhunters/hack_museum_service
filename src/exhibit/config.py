import os
from dataclasses import dataclass
from logging import getLogger

import yaml
import consul
from dotenv import load_dotenv

from exhibit import version

logger = getLogger(__name__)


class ConfigParseError(ValueError):
    pass


@dataclass
class PostgresConfig:
    DATABASE: str
    USERNAME: str
    PASSWORD: str
    HOST: str
    PORT: int = 5432


@dataclass
class S3Config:
    BUCKET: str
    ENDPOINT_URL: str
    PUBLIC_ENDPOINT_URL: str
    REGION: str
    ACCESS_KEY_ID: str
    ACCESS_KEY: str


@dataclass
class DbConfig:
    POSTGRESQL: PostgresConfig
    S3: S3Config


@dataclass
class ContactConfig:
    NAME: str = None
    URL: str = None
    EMAIL: str = None


@dataclass
class RabbitMQ:
    HOST: str
    PORT: int
    USERNAME: str
    PASSWORD: str
    VHOST: str


@dataclass
class ImgSearcherConfig:
    SEARCHER_TASKS_SENDER_ID: str
    SEARCHER_TASKS_RECEIVER_ID: str
    RABBITMQ: RabbitMQ


@dataclass
class JWTConfig:
    PUBLIC_KEY: str


@dataclass
class BaseConfig:
    TITLE: str
    DESCRIPTION: str
    VERSION: str
    SERVICE_PATH_PREFIX: str
    CONTACT: ContactConfig


@dataclass
class Config:
    DEBUG: bool
    JWT: JWTConfig
    BASE: BaseConfig
    IMG_SEARCHER: ImgSearcherConfig
    DB: DbConfig


def to_bool(value) -> bool:
    return str(value).strip().lower() in ("yes", "true", "t", "1")


def get_str_env(key: str, optional: bool = False) -> str:
    val = os.getenv(key)
    if not val and not optional:
        logger.error("%s is not set", key)
        raise ConfigParseError(f"{key} is not set")
    return val


def load_config() -> Config:
    """
    Load config from consul

    """
    env_file = ".env"

    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        logger.info("Loading env from os.environ")

    is_debug = to_bool(get_str_env('DEBUG'))
    root_name = get_str_env("CONSUL_ROOT")
    host = get_str_env("CONSUL_HOST")
    port = int(get_str_env("CONSUL_PORT"))
    service_path_prefix = get_str_env('SERVICE_PATH_PREFIX', optional=True)

    raw_yaml_config = consul.Consul(host=host, port=port, scheme="http").kv.get(root_name)[1]['Value'].decode("utf-8")
    if not raw_yaml_config:
        raise ConfigParseError("Consul config is empty")
    config = yaml.safe_load(raw_yaml_config)

    return Config(
        DEBUG=is_debug,
        BASE=BaseConfig(
            TITLE=config["base"]["title"],
            DESCRIPTION=config["base"]["description"],
            CONTACT=ContactConfig(
                NAME=config['base']['contact']['name'],
                URL=config['base']['contact']['url'],
                EMAIL=config['base']['contact']['email']
            ),
            VERSION=version.__version__,
            SERVICE_PATH_PREFIX=service_path_prefix
        ),
        JWT=JWTConfig(
            PUBLIC_KEY=config['jwt']['public_key'],
        ),
        DB=DbConfig(
            POSTGRESQL=PostgresConfig(
                HOST=config['database']['postgresql']['host'],
                PORT=config['database']['postgresql']['port'],
                USERNAME=config['database']['postgresql']['username'],
                PASSWORD=config['database']['postgresql']['password'],
                DATABASE=config['database']['postgresql']['database']
            ),
            S3=S3Config(
                ENDPOINT_URL=config['database']['s3']['endpoint_url'],
                REGION=config['database']['s3']['region'],
                ACCESS_KEY_ID=config['database']['s3']['access_key'],
                ACCESS_KEY=config['database']['s3']['secret_key'],
                BUCKET=config['database']['s3']['bucket'],
                PUBLIC_ENDPOINT_URL=config['database']['s3']['public_endpoint_url']
            ),
        ),
        IMG_SEARCHER=ImgSearcherConfig(
            SEARCHER_TASKS_SENDER_ID=config['img_searcher']['searcher_tasks_sender_id'],
            SEARCHER_TASKS_RECEIVER_ID=config['img_searcher']['searcher_tasks_receiver_id'],
            RABBITMQ=RabbitMQ(
                HOST=config['img_searcher']['rabbitmq']['host'],
                PORT=config['img_searcher']['rabbitmq']['port'],
                USERNAME=config['img_searcher']['rabbitmq']['username'],
                PASSWORD=config['img_searcher']['rabbitmq']['password'],
                VHOST=config['img_searcher']['rabbitmq']['vhost']
            )
        ),
    )
