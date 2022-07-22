import json
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
        film = await self._get_film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    async def get_list(
        self,
        sort: str = None,
        filter_genre: str = None,
        filter_person: str = None,
        page_size: int = 50,
        page_number: int = 1,
    ) -> list[Film]:
        params = f"{sort}/{filter_genre}/{filter_person}/{page_size}/{page_number}"
        films = await self._get_list_from_cache(params)
        if not films:
            resp = await self.elastic.search(index="movies", query={"match_all": {}}, size=page_size, sort=None)
            hits = resp.body.get("hits", {}).get("hits", [])
            films = [Film(**hit["_source"]) for hit in hits]
            if not films:
                return []
            await self._put_list_to_cache(params, films)
        return films

    async def _get_film_from_elastic(self, film_id: str) -> Film | None:
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return Film(**doc.body["_source"])

    async def _get_film_from_cache(self, film_id: str) -> Film | None:
        data = await self.redis.get(film_id)
        if not data:
            return None

        film = Film.parse_raw(data)
        return film

    async def _get_list_from_cache(self, params: str) -> list[Film]:
        data = await self.redis.get(params)
        if not data:
            return []

        return [Film.parse_raw(raw_film) for raw_film in json.loads(data)]

    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(film.id, film.json(), ex=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _put_list_to_cache(self, params, films: list[Film]):
        raw_films = [film.json() for film in films]
        await self.redis.set(params, json.dumps(raw_films), ex=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
