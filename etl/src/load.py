import logging
from typing import Any

import backoff
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, ConnectionTimeout, TransportError
from elasticsearch.helpers import bulk

from logger import logger
from models import EnvSettings, ElasticPersonsSchemaModel, ElasticMoviesSchemaModel
from state import BaseStorage
from transform import BatchTransform

settings = EnvSettings()


class ESLoader:
    """Класс, содержащий метод загрузки в elastic."""

    def __init__(self, transformer: BatchTransform, state: BaseStorage):
        self.transformer = transformer
        self.state = state
        self.elastic_connection = self.connect_to_es()

    @backoff.on_exception(
        exception=(ConnectionError, ConnectionTimeout, TransportError),
        wait_gen=backoff.expo,
        logger=logger,
        backoff_log_level=logging.ERROR,
    )
    def connect_to_es(self) -> Elasticsearch:
        logger.info("Соединение с Elasticsearch...")
        return Elasticsearch(hosts=settings.es_url, retry_on_timeout=False, max_retries=1)

    @backoff.on_exception(
        exception=(ConnectionError, ConnectionTimeout, TransportError),
        wait_gen=backoff.expo,
        on_backoff=connect_to_es,
        logger=logger,
        backoff_log_level=logging.ERROR,
    )
    def bulk_to_elastic(
        self,
        index: str,
        elastic_schema_models_batch: ElasticPersonsSchemaModel | ElasticMoviesSchemaModel,
        offset_name: str,
        offset: int,
    ):
        actions = [
            {
                "_index": index,
                "_id": film.id,
                "_source": film.json(),
            }
            for film in elastic_schema_models_batch
        ]

        self.state.save_state({offset_name: offset})
        logger.info(f"Записан batch длиной: {len(actions)}")
        bulk(self.elastic_connection, actions)

    def load_films_batch_to_elastic(self) -> None:
        """Метод загружает батчи данных по фильмам в elastic и сохраняет текущий offset."""

        for elastic_movies_schema_models_batch, films_offset in self.transformer.transform_film_data_batches():
            self.bulk_to_elastic(
                index="movies",
                elastic_schema_models_batch=elastic_movies_schema_models_batch,
                offset_name="films_offset",
                offset=films_offset,
            )

    def load_persons_batch_to_elastic(self) -> None:
        """Метод загружает батчи данных по актёрам в elastic и сохраняет текущий offset."""

        for transformed_persons_batch, persons_offset in self.transformer.transform_persons_data_batches():
            self.bulk_to_elastic(
                index="persons",
                elastic_schema_models_batch=transformed_persons_batch,
                offset_name="persons_offset",
                offset=persons_offset,
            )

    def load_genres_batch_to_elastic(self) -> None:
        """Метод загружает батчи данных по жанрам в elastic и сохраняет текущий offset."""

        for transformed_genres_batch, genres_offset in self.transformer.transform_genre_data_batches():
            self.bulk_to_elastic(
                index="genres",
                elastic_schema_models_batch=transformed_genres_batch,
                offset_name="genres_offset",
                offset=genres_offset,
            )
