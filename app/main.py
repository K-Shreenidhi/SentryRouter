from fastapi import FastAPI
from pydantic import BaseModel
from app.providers.mock_provider import MockProvider

app = FastAPI(title="SentryRouter")
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
async def chat_completions(req: ChatRequest):
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