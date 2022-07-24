from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.api_models import Person, PersonRoleInFilms

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5


class PersonsService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Person | None:
        person = await self._get_person_from_cache(person_id)
        if not person:
            person = await self._get_films_with_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        return person

    async def _get_person_from_cache(self, person_id: str) -> Person | None:
        data = await self.redis.get(person_id)
        if not data:
            return None

        genre = Person.parse_raw(data)
        return genre

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(person.id, person.json(), ex=PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_films_with_person_from_elastic(self, person_id: str) -> Person | None:
        try:
            person_doc = await self.elastic.get(index="persons", id=person_id)
        except NotFoundError:
            return None

        films_doc = await self.elastic.search(
            index="movies",
            body={
                "query": {
                    "bool": {
                        "should": [
                            {
                                "nested": {
                                    "path": "directors",
                                    "query": {"bool": {"should": {"term": {"directors.id": person_id}}}},
                                }
                            },
                            {
                                "nested": {
                                    "path": "writers",
                                    "query": {"bool": {"should": {"term": {"writers.id": person_id}}}},
                                }
                            },
                            {
                                "nested": {
                                    "path": "actors",
                                    "query": {"bool": {"should": {"term": {"actors.id": person_id}}}},
                                }
                            },
                        ]
                    }
                }
            },
        )

        hits_list = films_doc.body.get("hits", {}).get("hits", [])
        actor_films_ids = []
        writer_films_ids = []
        director_films_ids = []
        for hit in hits_list:
            source = hit["_source"]
            for actor_in_film in source["actors"]:
                if actor_in_film["id"] == person_id:
                    actor_films_ids.append(source["id"])
            for writer_in_film in source["writers"]:
                if writer_in_film["id"] == person_id:
                    writer_films_ids.append(source["id"])
            for director_in_film in source["directors"]:
                if director_in_film["id"] == person_id:
                    director_films_ids.append(source["id"])

        roles = []
        if actor_films_ids:
            roles.append(PersonRoleInFilms(role="actor", film_ids=actor_films_ids))
        if writer_films_ids:
            roles.append(PersonRoleInFilms(role="writer", film_ids=writer_films_ids))
        if director_films_ids:
            roles.append(PersonRoleInFilms(role="director", film_ids=director_films_ids))

        return Person(id=person_id, full_name=person_doc.body["_source"]["full_name"], roles=roles)


@lru_cache()
def get_persons_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonsService:
    return PersonsService(redis, elastic)
