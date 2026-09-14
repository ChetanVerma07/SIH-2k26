"""Simple in-memory TTL cache and a lightweight rate limiter.

Intentionally minimal — no external dependencies, no distributed cache.
Adequate for reducing repeated calls to a real weather API within a
single process, and for basic per-key request throttling.
"""
from __future__ import annotations
import time
from collections import deque
from threading import Lock
from typing import Any, Callable, Deque, Dict, Optional, Tuple


class TTLCache:
    def __init__(self, ttl_seconds: float = 300.0):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires_at, value = item
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.time() + self.ttl_seconds, value)

    def get_or_set(self, key: str, compute: Callable[[], Any]) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = compute()
        self.set(key, value)
        return value


class RateLimiter:
    """Simple fixed-window-ish limiter: max_calls per period_seconds, per key."""

    def __init__(self, max_calls: int = 30, period_seconds: float = 60.0):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self._calls: Dict[str, Deque[float]] = {}
        self._lock = Lock()

    def allow(self, key: str = "default") -> bool:
        now = time.time()
        with self._lock:
            q = self._calls.setdefault(key, deque())
            while q and now - q[0] > self.period_seconds:
                q.popleft()
            if len(q) >= self.max_calls:
                return False
            q.append(now)
            return True


class RateLimitExceeded(Exception):
    pass
