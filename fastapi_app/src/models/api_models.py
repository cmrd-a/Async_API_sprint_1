from models.common import Base, IdModel, Paginated, Person, Genre


class Film(IdModel):
    title: str


class FilmRated(Film):
    imdb_rating: float | None = 0.0


class FilmsByPerson(Base):
    films: list[FilmRated]


class PersonRoleInFilms(Base):
    role: str
    films_details: list[FilmRated]


class PersonWithFilms(IdModel):
    full_name: str
    roles: list[PersonRoleInFilms]


class PersonSearch(Paginated):
    persons_with_films: list[PersonWithFilms] | None


class FilmFull(FilmRated):
    description: str | None
    genres: list[Genre] | None
    actors: list[Person] | None
    writers: list[Person] | None
    directors: list[Person] | None


class FilmsRated(Paginated):
    results: list[FilmRated]


class GenreDescripted(Genre):
    description: str | None


class GenresDescripted(Base):
    genres: list[GenreDescripted]
