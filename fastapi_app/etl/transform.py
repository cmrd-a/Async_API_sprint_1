from extract import PGExtractor
from models import ElasticMoviesSchemaModel, ElasticPersonsSchemaModel, ElasticGenresSchemaModel


class BatchTransform:
    """Преобразует данные из extractor, в формат, пригодный для загрузки в elastic."""

    def __init__(self, extractor: PGExtractor):
        self.extractor = extractor

    def transform_film_data_batches(self) -> list[ElasticMoviesSchemaModel]:

        for modified_films_batch, offset in self.extractor.get_modified_films_batch():

            transformed_batch = []

            for film in modified_films_batch:

                unique_actors = []
                if film.actors:
                    unique_actors = [
                        dict(actors_tuple) for actors_tuple in {tuple(actors.items()) for actors in film.actors}
                    ]

                unique_writers = []
                if film.writers:
                    unique_writers = [
                        dict(writers_tuple) for writers_tuple in {tuple(writers.items()) for writers in film.writers}
                    ]

                transformed_batch.append(
                    ElasticMoviesSchemaModel(
                        id=film.fw_id,
                        imdb_rating=film.rating,
                        genre=film.genres,
                        title=film.title,
                        description=film.description,
                        director=film.directors[0] if film.directors else "",
                        actors_names=[actor["name"] for actor in unique_actors],
                        writers_names=[writer["name"] for writer in unique_writers],
                        actors=unique_actors,
                        writers=unique_writers,
                    )
                )

            yield transformed_batch, offset

    def transform_persons_data_batches(self) -> list[ElasticPersonsSchemaModel]:

        for modified_persons_batch, persons_offset in self.extractor.get_persons_batch():

            transformed_persons_batch = []

            for person in modified_persons_batch:
                transformed_persons_batch.append(
                    ElasticPersonsSchemaModel(
                        id=person.id,
                        full_name=person.full_name,
                    )
                )

            yield transformed_persons_batch, persons_offset

    def transform_genre_data_batches(self) -> list[ElasticGenresSchemaModel]:

        for modified_genres_batch, genres_offset in self.extractor.get_genres_batch():

            transformed_genres_batch = []

            for genre in modified_genres_batch:
                transformed_genres_batch.append(
                    ElasticGenresSchemaModel(
                        id=genre.id,
                        name=genre.name,
                        description=genre.description,
                    )
                )

            yield transformed_genres_batch, genres_offset
