from __future__ import annotations

from typing import Any


def build_spatial_planning_intelligence(timeline: list[dict[str, Any]], dependencies: dict[str, Any]) -> dict[str, Any]:
    critical_rows = [row for row in timeline if row.get("is_critical")]
    blocked_edges = [edge for edge in dependencies.get("edges", []) if edge.get("relation")]
    recommendations = []
    if critical_rows:
        recommendations.append("Prioriser les zones avec ETA ou workflow critique avant recalage planning.")
    if blocked_edges:
        recommendations.append("Vérifier les dépendances spatiales avant de lancer les lots aval.")
    if not recommendations:
        recommendations.append("Planning spatial sous contrôle. Continuer le suivi par zone.")
    return {
        "critical_path_count": len(critical_rows),
        "dependency_edges_count": len(blocked_edges),
        "recommendations": recommendations,
    }
