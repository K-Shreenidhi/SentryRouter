import json
import redis.asyncio as redis

class IdempotencyStore:
    def __init__(self, redis_client: redis.Redis, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl

    async def get(self, key: str) -> dict | None:
        val = await self.redis.get(f"idem:{key}")
        return json.loads(val) if val else None

    async def set(self, key: str, response: dict):
        await self.redis.set(f"idem:{key}", json.dumps(response), ex=self.ttl)