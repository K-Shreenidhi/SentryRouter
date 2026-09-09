from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import Header
from contextlib import asynccontextmanager
import redis.asyncio as redis
from app.providers.mock_provider import MockProvider
from app.core.rate_limiter import TokenBucketLimiter
from app.core.config import settings

limiter: TokenBucketLimiter | None = None
redis_client: redis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, limiter
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    limiter = TokenBucketLimiter(redis_client, capacity=10, refill_rate=1.0)  # 10 tokens, refills 1/sec
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

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest, x_api_key: str = Header(default="anonymous")):
    allowed = await limiter.allow(key=x_api_key, cost=1)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    result = await mock_provider.complete([m.model_dump() for m in req.messages])
    return result

# Debug-only controls — remove or gate these before anything resembling production
@app.post("/debug/mock/fail")
async def set_mock_fail(fail: bool = True):
    mock_provider.should_fail = fail
    return {"mock_should_fail": fail}

@app.post("/debug/mock/delay")
async def set_mock_delay(seconds: float = 0.0):
    mock_provider.delay_seconds = seconds
    return {"mock_delay_seconds": seconds}