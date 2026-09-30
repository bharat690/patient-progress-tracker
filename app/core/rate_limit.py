import time
from collections import defaultdict, deque
from threading import Lock

from app.core.config import (
    LOGIN_RATE_LIMIT,
    RAG_RATE_LIMIT,
    UPLOAD_RATE_LIMIT,
)


class RateLimitRule:
    def __init__(self, limit_value: str):
        parts = limit_value.strip().split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid rate limit format: {limit_value!r}")

        limit = int(parts[0])
        window = parts[1].lower()
        if window not in {"second", "minute", "hour", "day"}:
            raise ValueError(f"Unsupported rate limit window: {window!r}")

        bucket_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }[window]

        self.limit = limit
        self.window_seconds = bucket_seconds


class InMemoryRateLimiter:
    def __init__(self):
        self._buckets = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit_value: str) -> bool:
        rule = RateLimitRule(limit_value)
        now = time.monotonic()

        with self._lock:
            bucket = self._buckets[(key, limit_value)]
            while bucket and now - bucket[0] >= rule.window_seconds:
                bucket.popleft()

            if len(bucket) >= rule.limit:
                return False

            bucket.append(now)
            return True


rate_limiter = InMemoryRateLimiter()


def enforce_rate_limit(scope: str, key: str) -> None:
    mapping = {
        "RAG": RAG_RATE_LIMIT,
        "UPLOAD": UPLOAD_RATE_LIMIT,
        "LOGIN": LOGIN_RATE_LIMIT,
    }
    if scope not in mapping:
        raise ValueError(f"Unsupported rate limit scope: {scope}")

    if not rate_limiter.allow(key, mapping[scope]):
        raise PermissionError(
            f"Rate limit exceeded for {scope}. Try again later."
        )
