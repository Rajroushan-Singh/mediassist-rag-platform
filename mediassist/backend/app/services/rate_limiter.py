import collections
import hashlib
import math
import threading
import time
from typing import NamedTuple

from fastapi import Request

from app.config import settings


class RateLimitResult(NamedTuple):
    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    reset_epoch: int


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, limit: int = 10, window_seconds: int = 60) -> None:
        self.default_limit = limit
        self.default_window = window_seconds
        self._history: dict[str, collections.deque[float]] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def check(self, key: str) -> RateLimitResult:
        now = time.time()
        limit = settings.RATE_LIMIT_PER_MINUTE or self.default_limit
        window = settings.RATE_LIMIT_WINDOW_SECONDS or self.default_window

        with self._lock:
            # Periodic cleanup of stale keys
            if now - self._last_cleanup > 300:
                self._cleanup_stale(now, window)

            q = self._history.get(key)
            if q is None:
                q = collections.deque()
                self._history[key] = q

            # Evict timestamps outside the sliding window
            cutoff = now - window
            while q and q[0] <= cutoff:
                q.popleft()

            if len(q) >= limit:
                oldest_timestamp = q[0]
                retry_after = max(1, math.ceil(oldest_timestamp + window - now))
                reset_epoch = int(oldest_timestamp + window)
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after=retry_after,
                    reset_epoch=reset_epoch,
                )

            # Record request
            q.append(now)
            remaining = max(0, limit - len(q))
            reset_epoch = int(q[0] + window)

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                retry_after=0,
                reset_epoch=reset_epoch,
            )

    def _cleanup_stale(self, now: float, window: float) -> None:
        cutoff = now - window
        stale_keys = []
        for k, q in self._history.items():
            while q and q[0] <= cutoff:
                q.popleft()
            if not q:
                stale_keys.append(k)
        for k in stale_keys:
            self._history.pop(k, None)
        self._last_cleanup = now

    def reset(self) -> None:
        """Clear all rate limiting history."""
        with self._lock:
            self._history.clear()


rate_limiter = SlidingWindowRateLimiter()


def get_client_identifier(request: Request) -> str:
    """Extract a consistent identifier: token hash for authenticated users or IP address."""
    auth_header = request.headers.get("authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
            return f"user:{token_hash}"

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    return f"ip:{client_ip}"

