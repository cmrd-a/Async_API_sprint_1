from aioredis import Redis
from elasticsearch import AsyncElasticsearch


class PersonsService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

