from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.spatial.utils.normalization import normalize_spatial_value


RISK_STATUSES = {"AT_RISK", "BLOCKED"}
RISK_LEVELS = {"HIGH", "CRITICAL"}


def build_spatial_risk_heatmap(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {"actions_count": 0, "at_risk_count": 0, "blocked_count": 0, "critical_count": 0}
    )
    for action in actions:
        key = (
            normalize_spatial_value(action.get("batiment"), "batiment"),
            normalize_spatial_value(action.get("niveau"), "niveau"),
            normalize_spatial_value(action.get("piece"), "piece"),
        )
        bucket = grouped[key]
        bucket["actions_count"] += 1
        status = str(action.get("status") or "").upper()
        risk_level = str(action.get("risk_level") or "").upper()
        if status in RISK_STATUSES:
            bucket["at_risk_count"] += 1
        if status == "BLOCKED":
            bucket["blocked_count"] += 1
        if risk_level in RISK_LEVELS:
            bucket["critical_count"] += 1
    return [
        {
            "batiment": batiment,
            "niveau": niveau,
            "piece": piece,
            **values,
            "risk_score": min(100, values["at_risk_count"] * 25 + values["blocked_count"] * 35 + values["critical_count"] * 15),
        }
        for (batiment, niveau, piece), values in sorted(grouped.items())
    ]

