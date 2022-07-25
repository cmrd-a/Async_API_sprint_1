from functools import lru_cache

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.api_models import PersonWithFilms, PersonRoleInFilms, PersonSearch, FilmRated, FilmsByPerson
from services.common import RedisService


class PersonsService(RedisService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        RedisService.__init__(self, redis)
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> PersonWithFilms | None:
        redis_key = f"persons::person_id::{person_id}"
        person = await self._get_from_cache(key=redis_key, model=PersonWithFilms)
        if not person:
            person = await self._get_person_with_films_from_elastic(person_id)
            if not person:
                return None
            await self._put_to_cache(key=redis_key, obj=person)

        return person

    async def get_film_detail_by_person(self, person_id: str) -> FilmsByPerson | None:
        redis_key = f"movies::person_id::{person_id}"
        films_rated = await self._get_from_cache(key=redis_key, model=FilmsByPerson)

        if films_rated:
            return FilmsByPerson(films=films_rated.films)

        person_with_films = await self._get_film_details_by_person_id(person_id=person_id)

        if not person_with_films:
            return

        films = []
        for role in person_with_films.roles:
            films.extend(role.films_details)

        seen = set()
        films_rated = [seen.add(film.id) or film for film in films if film.id not in seen]

        if films_rated:
            films_rated_obj = FilmsByPerson(films=films_rated)
            await self._put_to_cache(key=redis_key, obj=films_rated_obj)
            return films_rated_obj

        return

    async def search(self, search_str: str, page_size: int = 50, page_number: int = 1) -> PersonSearch | None:
        redis_key = f"persons::search_str::{search_str}::page_size::{page_size}::page_number::{page_number}"
        person = await self._get_from_cache(key=redis_key, model=PersonSearch)
        if not person:
            person = await self._get_films_by_person_full_name_from_elastic(
                search_str=search_str,
                page_size=page_size,
                page_number=page_number,
            )
            if not person:
                return None
            await self._put_to_cache(key=redis_key, obj=person)

        return person

    async def _get_person_role_in_films(self, person_id: str) -> list[PersonRoleInFilms]:
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
            size=999,
        )

        hits_list = films_doc.body.get("hits", {}).get("hits", [])
        actor_films_details = []
        writer_films_details = []
        director_films_details = []
        for hit in hits_list:
            source = hit["_source"]
            for actor_in_film in source["actors"]:
                if actor_in_film["id"] == person_id:
                    actor_films_details.append(
                        FilmRated(
                            id=source["id"],
                            title=source["title"],
                            imdb_rating=source["imdb_rating"],
                        )
                    )
            for writer_in_film in source["writers"]:
                if writer_in_film["id"] == person_id:
                    writer_films_details.append(
                        FilmRated(
                            id=source["id"],
                            title=source["title"],
                            imdb_rating=source["imdb_rating"],
                        )
                    )
            for director_in_film in source["directors"]:
                if director_in_film["id"] == person_id:
                    director_films_details.append(
                        FilmRated(
                            id=source["id"],
                            title=source["title"],
                            imdb_rating=source["imdb_rating"],
                        )
                    )

        roles = []
        if actor_films_details:
            roles.append(PersonRoleInFilms(role="actor", films_details=actor_films_details))
        if writer_films_details:
            roles.append(PersonRoleInFilms(role="writer", films_details=writer_films_details))
        if director_films_details:
            roles.append(PersonRoleInFilms(role="director", films_details=director_films_details))

        return roles

    async def _get_film_details_by_person_id(self, person_id: str) -> PersonWithFilms | None:
        person_name = await self._get_person_name_from_elastic(person_id=person_id)

        if not person_name:
            return

        roles = await self._get_person_role_in_films(person_id=person_id)

        return PersonWithFilms(id=person_id, roles=roles, full_name=person_name)

    async def _get_films_by_person_full_name_from_elastic(
        self, search_str: str, page_size: int = 50, page_number: int = 1
    ) -> PersonSearch | None:

        persons_doc = await self.elastic.search(
            index="persons",
            query={"match": {"full_name": {"query": search_str}}},
            size=page_size,
            from_=(page_number - 1) * page_size if page_number > 1 else 0,
        )

        persons_hit_list = persons_doc.body.get("hits", {}).get("hits", [])
        total = persons_doc.body.get("hits", {})["total"]["value"]
        persons_with_films = []

        for person_hit in persons_hit_list:
            person_id = person_hit["_source"]["id"]
            person_name = person_hit["_source"]["full_name"]
            roles = await self._get_person_role_in_films(person_id=person_id)
            persons_with_films.append(PersonWithFilms(id=person_id, roles=roles, full_name=person_name))

        if not persons_with_films:
            return

        return PersonSearch(total=total, persons_with_films=persons_with_films)

    async def _get_person_with_films_from_elastic(self, person_id: str) -> PersonWithFilms | None:
        person_name = await self._get_person_name_from_elastic(person_id=person_id)

        if not person_name:
            return

        roles = await self._get_person_role_in_films(person_id=person_id)

        return PersonWithFilms(id=person_id, full_name=person_name, roles=roles)

    async def _get_person_name_from_elastic(self, person_id: str) -> str | None:
        try:
            person_doc = await self.elastic.get(index="persons", id=person_id)
        except NotFoundError:
            return None

        return person_doc.body["_source"]["full_name"]


@lru_cache()
def get_persons_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonsService:
    return PersonsService(redis, elastic)
