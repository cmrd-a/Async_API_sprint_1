from enum import Enum
from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.es_models import Film, FilmPaginated

# FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5
FILM_CACHE_EXPIRE_IN_SECONDS = 5


class ApiSortOptions(str, Enum):
    imdb_asc = "imdb"
    imdb_desc = "-imdb"


ElasticSortMap = {
    ApiSortOptions.imdb_asc: {"imdb_rating": {"order": "asc"}},
    ApiSortOptions.imdb_desc: {"imdb_rating": {"order": "desc"}},
}


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
        path,
        sort: ApiSortOptions | None,
        filter_genre: str = None,
        filter_person: str = None,
        page_size: int = 50,
        page_number: int = 1,
    ) -> FilmPaginated | None:
        redis_key = f"films/{path}"
        data = await self._get_list_from_cache(redis_key)
        if not data:
            filters = []
            if filter_genre:
                filters.append(
                    {"nested": {"path": "genres", "query": {"bool": {"must": {"term": {"genres.id": filter_genre}}}}}}
                )
            if filter_person:
                filters.append(
                    {
                        "bool": {
                            "should": [
                                {
                                    "nested": {
                                        "path": "actors",
                                        "query": {"bool": {"must": {"term": {"actors.id": filter_person}}}},
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "writers",
                                        "query": {"bool": {"must": {"term": {"writers.id": filter_person}}}},
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "directors",
                                        "query": {"bool": {"must": {"term": {"directors.id": filter_person}}}},
                                    }
                                },
                            ]
                        }
                    }
                )
            resp = await self.elastic.search(
                index="movies",
                query={"bool": {"must": filters}},
                sort=ElasticSortMap[sort] if sort else None,
                size=page_size,
                from_=(page_number - 1) * page_size if page_number > 1 else 0,
            )
            hits = resp.body.get("hits", {})
            total = resp.body.get("hits", {})["total"]["value"]
            _hits = hits.get("hits")
            if not _hits:
                return None
            films = [Film(**hit["_source"]) for hit in _hits]
            data = FilmPaginated(total=total, results=films)

            await self._put_list_to_cache(redis_key, data)
        return data

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

    async def _get_list_from_cache(self, params: str) -> FilmPaginated | None:
        data = await self.redis.get(params)
        if not data:
            return None

        return FilmPaginated.parse_raw(data)

    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(film.id, film.json(), ex=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _put_list_to_cache(self, params, films: FilmPaginated):
        await self.redis.set(params, films.json(), ex=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
