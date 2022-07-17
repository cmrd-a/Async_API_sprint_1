import os
from logging import config as logging_config

from pydantic import BaseSettings, Field

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_name: str = Field(env="PROJECT_NAME", default="movies")

    es_host: str = Field(env="ES_HOST", default="http://127.0.0.1")
    es_port: int = Field(env="ES_PORT", default=9200)

    redis_host: str = Field(env="REDIS_HOST", default="redis://127.0.0.1")
    redis_port: int = Field(env="REDIS_PORT", default=6379)

    @property
    def es_url(self):
        return f"{self.es_host}:{self.es_port}"

    @property
    def redis_url(self):
        return f"{self.redis_host}:{self.redis_port}"

    class Config:
        env_file = ".env"


config = Settings()
