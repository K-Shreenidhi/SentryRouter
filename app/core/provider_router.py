import asyncio
from app.core.circuit_breaker import CircuitBreaker
from app.providers.base import Provider, ProviderError

class ProviderRouter:
    """Tries providers in order, skipping any whose circuit breaker is OPEN.
    Records success/failure per provider so the breaker state reflects reality."""

    def __init__(self, providers: list[tuple[Provider, CircuitBreaker]], timeout_seconds: float = 2.0):
        self.providers = providers
        self.timeout_seconds = timeout_seconds

    async def complete(self, messages: list[dict]) -> dict:
        last_error = None
        for provider, breaker in self.providers:
            if not breaker.can_attempt():
                continue  # this provider's breaker is OPEN — skip it, don't even try
            try:
                result = await asyncio.wait_for(
                    provider.complete(messages), timeout=self.timeout_seconds
                )
                breaker.record_success()
                result["breaker_states"] = {p.name: b.state.value for p, b in self.providers}
                return result
            except (ProviderError, asyncio.TimeoutError) as e:
                breaker.record_failure()
                last_error = e
                continue  # try the next provider in line

        raise ProviderError(provider="all", retryable=False)