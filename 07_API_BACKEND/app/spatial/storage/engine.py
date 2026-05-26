from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_spatial_storage_intelligence(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"storage_impact": 0.0, "actions_count": 0, "risk_count": 0})
    for action in actions:
        zone = " > ".join(str(action.get(part) or "").strip() for part in ("batiment", "niveau", "piece") if str(action.get(part) or "").strip()) or "Zone non renseignée"
        bucket = grouped[zone]
        bucket["storage_impact"] += float(action.get("storage_impact") or 0)
        bucket["actions_count"] += 1
        if str(action.get("action_type") or "").upper() == "STORAGE" or str(action.get("status") or "").upper() in {"AT_RISK", "BLOCKED"}:
            bucket["risk_count"] += 1
    return [
        {
            "zone": zone,
            **values,
            "saturation_level": "HIGH" if values["risk_count"] >= 2 or values["storage_impact"] > 0 else "LOW",
            "message": "Risque de saturation stockage à coordonner." if values["risk_count"] >= 2 or values["storage_impact"] > 0 else "Stockage sans alerte majeure.",
        }
        for zone, values in sorted(grouped.items(), key=lambda item: (-item[1]["risk_count"], item[0]))
    ][:100]
