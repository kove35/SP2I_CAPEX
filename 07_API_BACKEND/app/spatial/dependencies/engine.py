from __future__ import annotations

from typing import Any


DEFAULT_DEPENDENCIES = {
    "DELIVERY": ["PROCUREMENT", "PLANNING"],
    "STORAGE": ["DELIVERY", "PLANNING"],
    "RISK": ["PLANNING", "QUALITY"],
    "PROCUREMENT": ["DELIVERY"],
    "PLANNING": ["COORDINATION"],
}


def build_spatial_dependency_graph(actions: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    by_zone_type: dict[tuple[str, str], str] = {}

    for action in actions:
        zone = " > ".join(str(action.get(part) or "").strip() for part in ("batiment", "niveau", "piece") if str(action.get(part) or "").strip()) or "Zone non renseignée"
        action_type = str(action.get("action_type") or "COORDINATION").upper()
        node_id = f"{zone}:{action_type}"
        nodes[node_id] = {
            "id": node_id,
            "zone": zone,
            "label": action_type,
            "status": action.get("status") or "TO_DO",
            "risk_level": action.get("risk_level") or "MEDIUM",
        }
        by_zone_type[(zone, action_type)] = node_id

    for (zone, action_type), source_id in by_zone_type.items():
        for target_type in DEFAULT_DEPENDENCIES.get(action_type, []):
            target_id = by_zone_type.get((zone, target_type))
            if target_id:
                edges.append({"source": source_id, "target": target_id, "relation": "spatial_sequence"})

    return {"nodes": list(nodes.values())[:200], "edges": edges[:300]}
