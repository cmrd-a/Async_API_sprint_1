import orjson
from pydantic import BaseModel, Field


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Base(BaseModel):
    id: str = Field(alias="uuid")

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
