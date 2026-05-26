from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_spatial_event_feed(actions: list[dict[str, Any]], timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    for action in actions:
        status = str(action.get("status") or "").upper()
        if status in {"AT_RISK", "BLOCKED"}:
            events.append(
                {
                    "event_type": "WORKFLOW_BLOCKED" if status == "BLOCKED" else "LOT_AT_RISK",
                    "severity": "critical" if status == "BLOCKED" else "warning",
                    "zone": _zone(action),
                    "entity_id": action.get("id"),
                    "message": action.get("problem") or action.get("title") or "Action chantier à surveiller.",
                    "recommended_action": action.get("recommended_action") or "Prioriser la coordination chantier.",
                    "created_at": now,
                }
            )
    for row in timeline:
        if row.get("is_critical"):
            events.append(
                {
                    "event_type": "ETA_RISK",
                    "severity": "warning",
                    "zone": row.get("zone"),
                    "entity_id": row.get("action_id"),
                    "message": row.get("message"),
                    "recommended_action": "Vérifier ETA, dépendances et stockage avant engagement.",
                    "created_at": now,
                }
            )
    return events[:50]


def _zone(action: dict[str, Any]) -> str:
    return " > ".join(str(action.get(part) or "").strip() for part in ("batiment", "niveau", "piece") if str(action.get(part) or "").strip()) or "Zone non renseignée"
