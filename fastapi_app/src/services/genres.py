import json
from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.es_models import GenreDescripted

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5


class GenresService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> GenreDescripted | None:
        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)

        return genre

    async def get_list(
        self,
    ) -> list[GenreDescripted]:
        genres = await self._get_list_from_cache()
        if not genres:
            resp = await self.elastic.search(index="genres", query={"match_all": {}}, sort=None)
            hits = resp.body.get("hits", {}).get("hits", [])
            genres = [GenreDescripted(**hit["_source"]) for hit in hits]
            if not genres:
                return []
            await self._put_list_to_cache(genres)
        return genres

    async def _get_genre_from_elastic(self, genre_id: str) -> GenreDescripted | None:
        try:
            doc = await self.elastic.get(index="genres", id=genre_id)
        except NotFoundError:
            return None
        return GenreDescripted(**doc.body["_source"])

    async def _get_genre_from_cache(self, genre_id: str) -> GenreDescripted | None:
        data = await self.redis.get(genre_id)
        if not data:
            return None

        genre = GenreDescripted.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: GenreDescripted):
        await self.redis.set(genre.id, genre.json(), ex=GENRE_CACHE_EXPIRE_IN_SECONDS)

    async def _get_list_from_cache(self) -> list[GenreDescripted]:
        data = await self.redis.get(name="genres")
        if not data:
            return []

        return [GenreDescripted.parse_raw(raw_genre) for raw_genre in json.loads(data)]

    async def _put_list_to_cache(self, genres: list[GenreDescripted]):
        raw_genres = [genre.json() for genre in genres]
        await self.redis.set(
            name="genres",
            value=json.dumps(raw_genres),
            ex=GENRE_CACHE_EXPIRE_IN_SECONDS,
        )


@lru_cache()
def get_genres_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenresService:
    return GenresService(redis, elastic)
