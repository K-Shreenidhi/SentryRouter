import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class ChatMessage(BaseModel):
    role: Role = Role.USER
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Target model ID (e.g., 'gpt-4o', 'claude-3-5-sonnet', 'mock')")
    messages: List[ChatMessage] = Field(..., min_length=1, description="Conversation history")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    stream: bool = False
    provider: Optional[ProviderType] = Field(
        default=None,
        description="Explicit provider override. If omitted, provider is resolved by model name."
    )
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatChoiceMessage(BaseModel):
    role: Role = Role.ASSISTANT
    content: str


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatChoiceMessage
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    provider: str
    choices: List[ChatChoice]
    usage: UsageInfo = Field(default_factory=UsageInfo)
    latency_ms: Optional[float] = None


class HealthStatus(BaseModel):
    status: str
    version: str = "0.1.0"
    postgres: str = "unknown"
    redis: str = "unknown"
