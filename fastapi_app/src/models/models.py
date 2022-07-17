from uuid import UUID

from pydantic import BaseModel


class UUIDMixin(BaseModel):
    id: UUID


class Person(UUIDMixin):
    name: str


class FilmWork(UUIDMixin):
    title: str
    description: str
    imdb_rating: int
    genre: list[str] = []
    actors_names: list[str] = []
    writers_names: list[str] = []
    writers: list[Person]
    actors: list[Person]
    director: str


class Genre(UUIDMixin):
    name: str
    description: str
