from typing import Type, TypeVar

from aioredis import Redis

from core.config import config
from models.common import Base

BaseTypeVar = TypeVar("BaseTypeVar", bound=Base)


class RedisService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.cache_expire_in_seconds = config.redis_cache_expire_in_seconds

    async def _put_to_cache(self, key: str, obj: BaseTypeVar):
        await self.redis.set(key, obj.json(), ex=self.cache_expire_in_seconds)

    async def _get_from_cache(self, key: str, model: Type[BaseTypeVar]) -> BaseTypeVar | None:
        data = await self.redis.get(key)
        if not data:
            return None

        parsed_data = model.parse_raw(data)
        return parsed_data
