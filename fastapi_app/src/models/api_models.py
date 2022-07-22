from models.common import Base


class Film(Base):
    title: str


class Genre(Base):
    name: str


class FilmByPerson(Base):
    title: str
    imdb_rating: float


class Person(Base):
    full_name: str
    role: str
    film_ids: list[str]
