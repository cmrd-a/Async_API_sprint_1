import logging
from datetime import datetime

import backoff
import psycopg2
import pytz
from psycopg2.extensions import cursor
from psycopg2.extras import NamedTupleCursor, RealDictRow

from logger import logger
from models import EnvSettings
from state import BaseStorage

settings = EnvSettings()

POSTGRES_CONNECTION = {
    "dbname": settings.pg_db_name,
    "user": settings.pg_db_user,
    "password": settings.pg_db_password,
    "host": settings.pg_db_host,
    "port": settings.pg_db_port,
}


class PGExtractor:
    """Получаем данные по фильмам из postgresql"""

    def __init__(self, batch_size: int, state: BaseStorage):

        self.batch_size = batch_size
        self.state = state
        self.cursor = self.pg_connection()

    @backoff.on_exception(
        exception=psycopg2.Error,
        wait_gen=backoff.expo,
        logger=logger,
        backoff_log_level=logging.ERROR,
    )
    def pg_connection(self) -> cursor:
        logger.info("Соединение с postgres...")
        postgres_connection = psycopg2.connect(**POSTGRES_CONNECTION, cursor_factory=NamedTupleCursor)
        return postgres_connection.cursor()

    @backoff.on_exception(
        exception=psycopg2.Error,
        wait_gen=backoff.expo,
        on_backoff=pg_connection,
    )
    def execute_query(self, query: str) -> list[RealDictRow]:
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except psycopg2.Error as exc:
            self.cursor = self.pg_connection()
            logger.exception(f"Ошибка извлечения данных из postgres: {exc}")
            raise exc

    def get_modified_films_batch(self) -> tuple[list[RealDictRow], int]:
        """Получаем фильмы, изменившиеся с момента last_extracting_time, батчами, по self.batch_size штук."""

        films_offset = self.state.retrieve_state().get("films_offset", 0)

        while True:
            # При первом переливе выставляем минимальную дату, для получения всех записей.
            films_last_extracting_time = self.state.retrieve_state().get(
                "films_last_extracting_time", datetime.min.replace(tzinfo=pytz.utc).isoformat()
            )

            query = f"""
                SELECT
                    fw.id as fw_id, 
                    fw.title, 
                    fw.description, 
                    fw.rating, 
                    fw.type, 
                    fw.created, 
                    fw.modified, 
                    ARRAY_AGG(JSON_BUILD_OBJECT(
                        'id', g.id, 
                        'name', g.name
                        )) as genres,
                    ARRAY_AGG(JSON_BUILD_OBJECT(
                        'id', p.id, 
                        'name', p.full_name
                        ))
                        FILTER (WHERE pfw.role = 'actor') AS actors,
                    ARRAY_AGG(JSON_BUILD_OBJECT(
                        'id', p.id, 
                        'name', p.full_name
                        ))
                        FILTER (WHERE pfw.role = 'director') AS directors,
                    ARRAY_AGG(JSON_BUILD_OBJECT(
                        'id', p.id, 
                        'name', p.full_name
                        ))
                        FILTER (WHERE pfw.role = 'writer') AS writers
                FROM content.film_work as fw
                LEFT JOIN content.person_film_work as pfw ON pfw.film_work_id = fw.id
                LEFT JOIN content.person as p ON p.id = pfw.person_id
                LEFT JOIN content.genre_film_work as gfw ON gfw.film_work_id = fw.id
                LEFT JOIN content.genre as g ON g.id = gfw.genre_id
                WHERE fw.modified > '{films_last_extracting_time}' 
                      OR g.modified > '{films_last_extracting_time}' 
                      OR p.modified > '{films_last_extracting_time}'
                GROUP BY fw.id
                ORDER BY fw_id
                OFFSET {films_offset}
                LIMIT {self.batch_size};
            """

            modified_films_batch = self.execute_query(query)

            if not modified_films_batch:
                films_last_extracting_time = datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()
                logger.info(f"Фильмы не изменялись. Дата проверки {films_last_extracting_time}")
                self.state.save_state(
                    {
                        "films_last_extracting_time": films_last_extracting_time,
                        "films_offset": 0,
                    }
                )
                break

            modified_films_batch_len = len(modified_films_batch)
            films_offset += modified_films_batch_len

            yield modified_films_batch, films_offset

            if modified_films_batch_len < self.batch_size:
                break

    def get_persons_batch(self):
        """Получаем актеров, данные по которым изменились с момента persons_last_extracting_time,
        батчами, по self.batch_size штук.
        """

        persons_offset = self.state.retrieve_state().get("persons_offset", 0)

        while True:
            # При первом переливе выставляем минимальную дату, для получения всех записей.
            persons_last_extracting_time = self.state.retrieve_state().get(
                "persons_last_extracting_time", datetime.min.replace(tzinfo=pytz.utc).isoformat()
            )

            query = f"""
                SELECT id, full_name
                FROM content.person
                WHERE modified > '{persons_last_extracting_time}'
                OFFSET {persons_offset}
                LIMIT {self.batch_size};
            """

            modified_persons_batch = self.execute_query(query)

            if not modified_persons_batch:
                persons_last_extracting_time = datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()
                logger.info(f"Данные по актерам не изменялись. Дата проверки {persons_last_extracting_time}")
                self.state.save_state(
                    {
                        "persons_last_extracting_time": persons_last_extracting_time,
                        "persons_offset": 0,
                    }
                )
                break

            modified_persons_batch_len = len(modified_persons_batch)
            persons_offset += modified_persons_batch_len

            yield modified_persons_batch, persons_offset

            if modified_persons_batch_len < self.batch_size:
                break

    def get_genres_batch(self):
        """Получаем жанры, данные по которым изменились с момента genres_last_extracting_time,
        батчами, по self.batch_size штук.
        """

        genres_offset = self.state.retrieve_state().get("genres_offset", 0)

        while True:
            # При первом переливе выставляем минимальную дату, для получения всех записей.
            genres_last_extracting_time = self.state.retrieve_state().get(
                "genres_last_extracting_time", datetime.min.replace(tzinfo=pytz.utc).isoformat()
            )

            query = f"""
                SELECT id, name, description
                FROM content.genre
                WHERE modified > '{genres_last_extracting_time}'
                OFFSET {genres_offset}
                LIMIT {self.batch_size};
            """

            modified_genres_batch = self.execute_query(query)

            if not modified_genres_batch:
                genres_last_extracting_time = datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()
                logger.info(f"Данные по жанрам не изменялись. Дата проверки {genres_last_extracting_time}")
                self.state.save_state(
                    {
                        "genres_last_extracting_time": genres_last_extracting_time,
                        "genres_offset": 0,
                    }
                )
                break

            modified_genres_batch_len = len(modified_genres_batch)
            genres_offset += modified_genres_batch_len

            yield modified_genres_batch, genres_offset

            if modified_genres_batch_len < self.batch_size:
                break
