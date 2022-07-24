import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Base(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class IdModel(Base):
    id: str


class Paginated(Base):
    total: int = 0


class Person(IdModel):
    name: str


class Genre(IdModel):
    name: str
