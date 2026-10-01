import time
from collections import defaultdict

from fastapi import Request

from app.core.errors import RateLimitExceededError


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter per client IP."""
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> None:
        now = time.time()
        cutoff = now - window_seconds
        # Evict timestamps older than window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= max_requests:
            raise RateLimitExceededError(
                f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s."
            )

        self._requests[key].append(now)

    def get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"


limiter = SlidingWindowRateLimiter()
