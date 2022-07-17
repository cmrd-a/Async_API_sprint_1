from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.es_models import FilmWork

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> FilmWork | None:
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str) -> FilmWork | None:
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return FilmWork(**doc.body["_source"])

    async def _film_from_cache(self, film_id: str) -> FilmWork | None:
        data = await self.redis.get(film_id)
        if not data:
            return None

        film = FilmWork.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: FilmWork):
        await self.redis.set(film.id, film.json(), ex=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis), elastic: AsyncElasticsearch = Depends(get_elastic)
) -> FilmService:
    return FilmService(redis, elastic)
