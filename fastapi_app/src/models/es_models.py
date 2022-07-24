from models.common import IdModel, Paginated, Person, Genre


class Film(IdModel):
    title: str
    description: str | None
    imdb_rating: float | None = 0.0
    genres: list[Genre] = []
    actors_names: list[str] | None = None
    writers_names: list[str] | None = None
    writers: list[Person] | None
    actors: list[Person] | None
    directors: list[Person] | None


class GenreDescripted(Genre):
    description: str | None


class FilmPaginated(Paginated):
    results: list[Film]
