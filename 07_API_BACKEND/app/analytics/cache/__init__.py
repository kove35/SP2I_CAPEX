from __future__ import annotations

import sys
import time
from typing import Any


class AnalyticsCache:
    """Petit cache memoire prepare pour etre remplace par Redis en V2."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._metrics = {
            "lookup_count": 0,
            "lookup_ms": 0.0,
            "hit_count": 0,
            "miss_count": 0,
            "write_count": 0,
            "write_ms": 0.0,
            "last_lookup_at": None,
            "last_write_at": None,
            "last_cleared_at": None,
        }

    def _elapsed_ms(self, start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 2)

    def get(self, key: str) -> Any | None:
        start = time.perf_counter()
        self._metrics["lookup_count"] += 1
        item = self._store.get(key)
        elapsed_ms = self._elapsed_ms(start)
        self._metrics["lookup_ms"] += elapsed_ms
        self._metrics["last_lookup_at"] = time.time()

        if not item:
            self._metrics["miss_count"] += 1
            return None

        created_at, value = item
        if time.time() - created_at > self.ttl_seconds:
            self._store.pop(key, None)
            self._metrics["miss_count"] += 1
            return None

        self._metrics["hit_count"] += 1
        return value

    def set(self, key: str, value: Any) -> None:
        start = time.perf_counter()
        self._store[key] = (time.time(), value)
        elapsed_ms = self._elapsed_ms(start)
        self._metrics["write_count"] += 1
        self._metrics["write_ms"] += elapsed_ms
        self._metrics["last_write_at"] = time.time()

    def peek(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        return item[1]

    def keys(self) -> list[str]:
        return sorted(self._store.keys())

    def clear(self) -> None:
        """Vide le cache apres une synchronisation PostgreSQL."""
        self._store.clear()
        self._metrics["last_cleared_at"] = time.time()

    def _estimated_memory_usage_mb(self) -> float:
        size = 0
        for key, item in self._store.items():
            size += sys.getsizeof(key)
            size += sys.getsizeof(item)
        return round(size / 1024 / 1024, 4)

    def status(self) -> dict[str, Any]:
        lookup_count = self._metrics["lookup_count"]
        hit_rate = round(self._metrics["hit_count"] / lookup_count, 3) if lookup_count else None
        return {
            "backend": "in-memory",
            "cache_entries": len(self._store),
            "entries": len(self._store),
            "ttl_seconds": self.ttl_seconds,
            "redis_ready": False,
            "keys": self.keys(),
            "memory_usage_mb": self._estimated_memory_usage_mb(),
            "warm": bool(self._store),
            "cache_lookup_ms": round(self._metrics["lookup_ms"], 2),
            "cache_write_ms": round(self._metrics["write_ms"], 2),
            "cache_hits": self._metrics["hit_count"],
            "cache_misses": self._metrics["miss_count"],
            "cache_hit_rate": hit_rate,
            "last_lookup_at": self._metrics["last_lookup_at"],
            "last_write_at": self._metrics["last_write_at"],
            "last_cleared_at": self._metrics["last_cleared_at"],
        }


analytics_cache = AnalyticsCache()
