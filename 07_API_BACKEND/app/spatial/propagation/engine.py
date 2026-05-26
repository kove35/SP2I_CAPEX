from __future__ import annotations

from typing import Any


def build_spatial_risk_propagation(events: list[dict[str, Any]], dependencies: dict[str, Any]) -> list[dict[str, Any]]:
    chains: list[dict[str, Any]] = []
    for event in events[:20]:
        zone = event.get("zone") or "Zone non renseignée"
        chains.append(
            {
                "source_event": event.get("event_type"),
                "zone": zone,
                "severity": event.get("severity", "info"),
                "chain": [zone, "Lots dépendants", "Planning chantier", "Réception"],
                "message": "Impact spatial à surveiller sur le workflow aval.",
            }
        )
    if not chains and dependencies.get("edges"):
        chains.append(
            {
                "source_event": "DEPENDENCY_GRAPH",
                "zone": "Projet",
                "severity": "info",
                "chain": ["Approvisionnement", "Pose", "Validation", "Réception"],
                "message": "Dépendances spatiales détectées sans alerte bloquante.",
            }
        )
    return chains
