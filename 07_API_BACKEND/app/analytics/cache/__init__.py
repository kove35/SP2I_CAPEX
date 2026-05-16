from __future__ import annotations

import time
from typing import Any


class AnalyticsCache:
    """Petit cache memoire prepare pour etre remplace par Redis en V2."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        created_at, value = item
        if time.time() - created_at > self.ttl_seconds:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)

    def status(self) -> dict[str, Any]:
        return {
            "backend": "in-memory",
            "entries": len(self._store),
            "ttl_seconds": self.ttl_seconds,
            "redis_ready": False,
        }


analytics_cache = AnalyticsCache()
