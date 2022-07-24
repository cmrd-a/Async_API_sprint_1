from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.api_models import GenreDescripted, GenresDescripted
from services.common import RedisService


class GenresService(RedisService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        RedisService.__init__(self, redis)
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> GenreDescripted | None:
        genre = await self._get_from_cache(key=genre_id, model=GenreDescripted)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_to_cache(key=genre_id, obj=genre)

        return genre

    async def get_list(
        self,
    ) -> GenresDescripted | None:
        genres = await self._get_from_cache(key="genres", model=GenresDescripted)

        if not genres:
            resp = await self.elastic.search(index="genres", query={"match_all": {}}, sort=None)
            hits = resp.body.get("hits", {}).get("hits", [])
            genres = [GenreDescripted(**hit["_source"]) for hit in hits]

            if not genres:
                return

            genres = GenresDescripted(genres=genres)
            await self._put_to_cache(key="genres", obj=genres)

        return genres

    async def _get_genre_from_elastic(self, genre_id: str) -> GenreDescripted | None:
        try:
            doc = await self.elastic.get(index="genres", id=genre_id)
        except NotFoundError:
            return None
        return GenreDescripted(**doc.body["_source"])


@lru_cache()
def get_genres_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenresService:
    return GenresService(redis, elastic)
