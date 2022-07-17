from models.common import Base


class Person(Base):
    name: str


class FilmWork(Base):
    title: str
    description: str
    imdb_rating: int
    genre: list[str] = []
    actors_names: list[str] = []
    writers_names: list[str] = []
    writers: list[Person]
    actors: list[Person]
    director: list[str] = []


class Genre(Base):
    name: str
    description: str
