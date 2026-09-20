import time
from enum import Enum

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 15.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = State.CLOSED
        self.opened_at: float | None = None

    def can_attempt(self) -> bool:
        if self.state == State.CLOSED:
            return True
        if self.state == State.OPEN:
            if time.time() - self.opened_at >= self.recovery_timeout:
                self.state = State.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN — allow exactly one probe through

    def record_success(self):
        self.failures = 0
        self.state = State.CLOSED

    def record_failure(self):
        self.failures += 1
        if self.state == State.HALF_OPEN or self.failures >= self.failure_threshold:
            self.state = State.OPEN
            self.opened_at = time.time()