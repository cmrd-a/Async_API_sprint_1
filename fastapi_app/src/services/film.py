from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.es_models import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Film | None:
        film = await self._get_from_cache(film_id)
        if not film:
            film = await self._get_from_elastic(film_id)
            if not film:
                return None
            await self._put_to_cache(film)

        return film

    async def get_list(
        self, sort: str, filter_genre: str, filter_person: str, page_size: int = 50, page_number: int = 1
    ) -> list[Film]:
        resp = await self.elastic.search(index="movies", query={"match_all": {}}, size=page_size, sort=None)
        hits = resp.body.get("hits", {}).get("hits", [])
        return [Film(**hit["_source"]) for hit in hits]

    async def _get_from_elastic(self, film_id: str) -> Film | None:
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return Film(**doc.body["_source"])

    async def _get_from_cache(self, film_id: str) -> Film | None:
        data = await self.redis.get(film_id)
        if not data:
            return None

        film = Film.parse_raw(data)
        return film

    async def _put_to_cache(self, film: Film):
        await self.redis.set(film.id, film.json(), ex=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis), elastic: AsyncElasticsearch = Depends(get_elastic)
) -> FilmService:
    return FilmService(redis, elastic)
