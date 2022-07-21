from time import sleep

from extract import PGExtractor
from load import ESLoader
from state import JsonFileStorage
from transform import BatchTransform


if __name__ == "__main__":

    storage = JsonFileStorage("state/state.json")
    pg_extractor = PGExtractor(batch_size=500, state=storage)
    batch_transform = BatchTransform(extractor=pg_extractor)
    es_loader = ESLoader(transformer=batch_transform, state=storage)

    while True:
        es_loader.load_films_batch_to_elastic()
        es_loader.load_persons_batch_to_elastic()
        es_loader.load_genres_batch_to_elastic()
        sleep(60)
