"""In-process sliding-window rate limiter for analysis endpoints."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from app.config import settings
from app.core.errors import RateLimitError


class SlidingWindowLimiter:
    """Simple per-client limiter. Replace with Redis for multi-worker deploys."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, client_id: str) -> None:
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[client_id]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - bucket[0])) + 1
                raise RateLimitError(
                    f"API request limit reached ({self.max_requests} requests per "
                    f"{self.window_seconds}s). Please wait {retry_after}s and try again."
                )
            bucket.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
