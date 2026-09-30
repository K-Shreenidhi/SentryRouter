import asyncio
import hashlib
import json
import redis.asyncio as redis

class SingleFlight:
    def __init__(self, redis_client: redis.Redis, lock_timeout: int = 10):
        self.redis = redis_client
        self.lock_timeout = lock_timeout

    def _key(self, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get_or_compute(self, payload: dict, compute_fn):
        cache_key = f"cache:{self._key(payload)}"
        lock_key = f"lock:{self._key(payload)}"

        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        got_lock = await self.redis.set(lock_key, "1", nx=True, ex=self.lock_timeout)
        if got_lock:
            try:
                result = await compute_fn()
                await self.redis.set(cache_key, json.dumps(result), ex=3600)
                return result
            finally:
                await self.redis.delete(lock_key)
        else:
            for _ in range(self.lock_timeout * 10):
                await asyncio.sleep(0.1)
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            return await compute_fn()  # lock holder died without writing