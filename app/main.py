from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import Header
from contextlib import asynccontextmanager
import redis.asyncio as redis
from app.core.circuit_breaker import CircuitBreaker
from app.core.provider_router import ProviderRouter
from app.providers.base import ProviderError
from app.providers.mock_provider import MockProvider
from app.core.rate_limiter import TokenBucketLimiter
from app.core.config import settings
from app.core.idempotency import IdempotencyStore
from app.core.singleflight import SingleFlight

limiter: TokenBucketLimiter | None = None
redis_client: redis.Redis | None = None

idempotency_store: IdempotencyStore | None = None
singleflight: SingleFlight | None = None

provider_a = MockProvider()
provider_a.name = "provider-a"
provider_b = MockProvider()
provider_b.name = "provider-b"

breaker_a = CircuitBreaker(name="provider-a", failure_threshold=3, recovery_timeout=15.0)
breaker_b = CircuitBreaker(name="provider-b", failure_threshold=3, recovery_timeout=15.0)

router = ProviderRouter(providers=[(provider_a, breaker_a), (provider_b, breaker_b)])





@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, limiter, idempotency_store, singleflight
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    limiter = TokenBucketLimiter(redis_client, capacity=10, refill_rate=1.0)  # 10 tokens, refills 1/sec
    idempotency_store = IdempotencyStore(redis_client)
    singleflight = SingleFlight(redis_client)
    yield
    await redis_client.close()


app = FastAPI(title="SentryRouter", lifespan=lifespan)
mock_provider = MockProvider()


@app.get("/")
async def root():
    return {
        "service": "SentryRouter",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 0.0

@app.post("/v1/chat/completions")
async def chat_completions(
    req: ChatRequest,
    x_api_key: str = Header(default="anonymous"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key:
        cached = await idempotency_store.get(idempotency_key)
        if cached:
            return cached

    allowed = await limiter.allow(key=x_api_key, cost=1)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    async def call_router():
        try:
            return await router.complete([m.model_dump() for m in req.messages])
        except ProviderError:
            raise HTTPException(status_code=503, detail="All providers unavailable")

    if req.temperature == 0.0:
        payload = {"messages": [m.model_dump() for m in req.messages], "temperature": 0.0}
        result = await singleflight.get_or_compute(payload, call_router)
    else:
        result = await call_router()

    if idempotency_key:
        await idempotency_store.set(idempotency_key, result)

    return result

# Debug-only controls — remove or gate these before anything resembling production
@app.post("/debug/provider-a/fail")
async def set_a_fail(fail: bool = True):
    provider_a.should_fail = fail
    return {"provider_a_should_fail": fail}

@app.post("/debug/provider-a/delay")
async def set_a_delay(seconds: float = 0.0):
    provider_a.delay_seconds = seconds
    return {"provider_a_delay_seconds": seconds}

@app.post("/debug/provider-b/fail")
async def set_b_fail(fail: bool = True):
    provider_b.should_fail = fail
    return {"provider_b_should_fail": fail}

@app.post("/debug/provider-b/delay")
async def set_b_delay(seconds: float = 0.0):
    provider_b.delay_seconds = seconds
    return {"provider_b_delay_seconds": seconds}

@app.get("/debug/breaker-states")
async def breaker_states():
    return {"provider-a": breaker_a.state.value, "provider-b": breaker_b.state.value}