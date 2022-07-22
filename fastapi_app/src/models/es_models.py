from models.common import Base


class Person(Base):
    name: str


class Film(Base):
    title: str
    description: str | None
    imdb_rating: int | None
    genre: list[str] = []
    actors_names: list[str] | None = None
    writers_names: list[str] | None = None
    writers: list[Person] | None
    actors: list[Person] | None
    director: list[str] | str | None


class Genre(Base):
    name: str
    description: str | None
