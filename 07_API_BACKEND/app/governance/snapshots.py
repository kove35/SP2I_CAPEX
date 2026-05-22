from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JsonSnapshotStore:
    """Petit stockage JSON pour afficher un etat SNAPSHOT si le live ralentit."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = {
            "analytics_state": "SNAPSHOT",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        (self.root / f"{name}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        return snapshot

    def read(self, name: str) -> dict[str, Any] | None:
        path = self.root / f"{name}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None
