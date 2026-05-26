from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.spatial.utils.normalization import make_spatial_key, normalize_spatial_value


SPATIAL_LEVELS = ("batiment", "niveau", "appart", "piece", "lot", "objet_bim")


class SpatialHierarchyEngine:
    """Builds a progressive spatial hierarchy without requiring BIM data."""

    def __init__(self, levels: tuple[str, ...] = SPATIAL_LEVELS) -> None:
        self.levels = levels

    def build_tree(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        root: dict[str, dict[str, Any]] = {}
        for row in rows:
            branch = root
            parent_key = ""
            for level in self.levels:
                raw_value = row.get(level)
                if not raw_value and level == "objet_bim":
                    raw_value = row.get("ifc_guid") or row.get("bim_object_id")
                value = normalize_spatial_value(raw_value, level)
                key = make_spatial_key(parent_key, level, value)
                if key not in branch:
                    branch[key] = {
                        "id": key,
                        "level": level,
                        "label": value,
                        "capex_local": 0.0,
                        "lines_count": 0,
                        "risk_count": 0,
                        "children": {},
                    }
                node = branch[key]
                node["capex_local"] = round(float(node["capex_local"]) + float(row.get("capex_local") or 0), 2)
                node["lines_count"] = int(node["lines_count"]) + int(row.get("lines_count") or 1)
                node["risk_count"] = int(node["risk_count"]) + int(row.get("risk_count") or 0)
                branch = node["children"]
                parent_key = key
        return [self._freeze_node(node) for node in root.values()]

    def aggregate_by_level(self, rows: list[dict[str, Any]], level: str) -> list[dict[str, Any]]:
        if level not in self.levels:
            level = "lot"
        grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"capex_local": 0.0, "lines_count": 0, "risk_count": 0})
        for row in rows:
            value = row.get(level)
            if not value and level == "objet_bim":
                value = row.get("ifc_guid") or row.get("bim_object_id")
            label = normalize_spatial_value(value, level)
            grouped[label]["capex_local"] += float(row.get("capex_local") or 0)
            grouped[label]["lines_count"] += int(row.get("lines_count") or 1)
            grouped[label]["risk_count"] += int(row.get("risk_count") or 0)
        return [
            {
                "level": level,
                "label": label,
                "capex_local": round(values["capex_local"], 2),
                "lines_count": values["lines_count"],
                "risk_count": values["risk_count"],
            }
            for label, values in sorted(grouped.items(), key=lambda item: (-item[1]["capex_local"], item[0]))
        ]

    def _freeze_node(self, node: dict[str, Any]) -> dict[str, Any]:
        return {
            **node,
            "children": [self._freeze_node(child) for child in node["children"].values()],
        }

