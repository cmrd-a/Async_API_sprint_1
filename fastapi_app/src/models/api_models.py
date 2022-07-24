from models.common import Base, IdModel, Paginated, Person, Genre


class PersonRoleInFilms(Base):
    role: str
    film_ids: list[str]


class PersonRoles(IdModel):
    full_name: str
    roles: list[PersonRoleInFilms]


class Film(IdModel):
    title: str


class FilmRated(Film):
    imdb_rating: float | None = 0.0


class FilmFull(FilmRated):
    description: str | None
    genres: list[Genre] | None
    actors: list[Person] | None
    writers: list[Person] | None
    directors: list[Person] | None


class FilmsRated(Paginated):
    results: list[FilmRated]
