from __future__ import annotations

import time
from typing import Any


class WorkflowCache:
    def __init__(self, ttl_seconds: int = 15) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[int, tuple[float, dict[str, Any]]] = {}

    def get(self, project_id: int) -> dict[str, Any] | None:
        item = self._items.get(project_id)
        if not item:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self.invalidate(project_id)
            return None
        return value

    def set(self, project_id: int, value: dict[str, Any]) -> dict[str, Any]:
        self._items[project_id] = (time.time() + self.ttl_seconds, value)
        return value

    def invalidate(self, project_id: int | None = None) -> None:
        if project_id is None:
            self._items.clear()
            return
        self._items.pop(project_id, None)


workflow_cache = WorkflowCache()
