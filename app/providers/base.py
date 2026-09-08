from abc import ABC, abstractmethod

class ProviderException(Exception):
    def __init__(self, provider: str, retryable: bool = True):
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"{provider} failed (retryable={retryable})")

# Backward-compat alias used by mock_provider
ProviderError = ProviderException

class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, messages: list[dict]) -> dict:
        ...

# Backward-compat alias used by mock_provider
Provider = BaseLLMProvider