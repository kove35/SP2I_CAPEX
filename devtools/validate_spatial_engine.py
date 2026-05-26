from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.spatial.hierarchy.engine import SpatialHierarchyEngine
from app.spatial.dependencies.engine import build_spatial_dependency_graph
from app.spatial.events.engine import build_spatial_event_feed
from app.spatial.planning.engine import build_spatial_planning_intelligence
from app.spatial.propagation.engine import build_spatial_risk_propagation
from app.spatial.risks.propagation import build_spatial_risk_heatmap
from app.spatial.storage.engine import build_spatial_storage_intelligence
from app.spatial.timeline.engine import build_spatial_timeline
from app.spatial.utils.normalization import normalize_spatial_value


def assert_equal(label: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> None:
    rows = [
        {"batiment": "A", "niveau": "RDC", "appart": "A001", "piece": "Cuisine", "lot": "Plomberie", "capex_local": 1000, "lines_count": 1},
        {"batiment": "A", "niveau": "RDC", "appart": "A001", "piece": "Cuisine", "lot": "Electricite", "capex_local": 1500, "lines_count": 1},
        {"batiment": "B", "niveau": "R+1", "appart": "", "piece": "", "lot": "Facade", "capex_local": 3000, "lines_count": 2},
    ]
    engine = SpatialHierarchyEngine()
    tree = engine.build_tree(rows)
    assert_equal("root nodes", len(tree), 2)
    by_batiment = engine.aggregate_by_level(rows, "batiment")
    assert_equal("first batiment", by_batiment[0]["label"], "B")
    assert_equal("capex B", by_batiment[0]["capex_local"], 3000.0)
    assert_equal("fallback piece", normalize_spatial_value("", "piece"), "Pièce non renseignée")

    heatmap = build_spatial_risk_heatmap(
        [
            {
                "id": 1,
                "batiment": "A",
                "niveau": "RDC",
                "piece": "Cuisine",
                "lot": "Plomberie",
                "status": "AT_RISK",
                "risk_level": "HIGH",
                "action_type": "DELIVERY",
                "delivery_eta_days": 12,
                "storage_impact": 1,
                "problem": "Retard livraison plomberie",
            },
            {
                "id": 2,
                "batiment": "A",
                "niveau": "RDC",
                "piece": "Cuisine",
                "lot": "Plomberie",
                "status": "BLOCKED",
                "risk_level": "CRITICAL",
                "action_type": "PLANNING",
                "delivery_eta_days": 5,
            },
        ]
    )
    assert_equal("heatmap buckets", len(heatmap), 1)
    assert_equal("blocked count", heatmap[0]["blocked_count"], 1)

    actions = [
        {
            "id": 1,
            "batiment": "A",
            "niveau": "RDC",
            "piece": "Cuisine",
            "lot": "Plomberie",
            "status": "AT_RISK",
            "risk_level": "HIGH",
            "action_type": "DELIVERY",
            "delivery_eta_days": 12,
            "storage_impact": 1,
            "problem": "Retard livraison plomberie",
        },
        {
            "id": 2,
            "batiment": "A",
            "niveau": "RDC",
            "piece": "Cuisine",
            "lot": "Plomberie",
            "status": "TO_DO",
            "risk_level": "MEDIUM",
            "action_type": "PLANNING",
            "delivery_eta_days": 5,
        },
    ]
    timeline = build_spatial_timeline(actions)
    assert_equal("timeline rows", len(timeline), 2)
    dependencies = build_spatial_dependency_graph(actions)
    assert_equal("dependency edges", len(dependencies["edges"]), 1)
    events = build_spatial_event_feed(actions, timeline)
    if not events:
        raise AssertionError("event feed should include timeline or risk events")
    planning = build_spatial_planning_intelligence(timeline, dependencies)
    if planning["critical_path_count"] < 1:
        raise AssertionError("planning should detect a critical path")
    storage = build_spatial_storage_intelligence(actions)
    assert_equal("storage buckets", len(storage), 1)
    propagation = build_spatial_risk_propagation(events, dependencies)
    if not propagation:
        raise AssertionError("risk propagation should produce at least one chain")

    print("OK - spatial hierarchy, timeline, event, storage and propagation engines are valid.")


if __name__ == "__main__":
    main()
