from __future__ import annotations

from typing import Any


class ConsolidationEngine:
    """Decide groupage ou expedition separee."""

    def evaluate(self, lignes: list[dict[str, Any]]) -> dict[str, Any]:
        if not lignes:
            return {
                "strategy": "NO_SHIPMENT",
                "reason": "Aucune ligne a consolider.",
                "risk_level": "LOW",
                "estimated_delay_risk": 0,
            }

        ports = {str(ligne.get("supplier_city") or ligne.get("departure_port") or "Shanghai") for ligne in lignes}
        max_delay = max(self._number(ligne.get("supplier_availability_days"), 0) for ligne in lignes)
        critical = any(str(ligne.get("project_criticality") or "").upper() in {"HIGH", "CRITICAL"} for ligne in lignes)

        if len(ports) == 1 and max_delay <= 10 and not critical:
            return {
                "strategy": "GROUPED_SHIPMENT",
                "reason": "Fournisseurs proches et disponibilites compatibles.",
                "risk_level": "LOW",
                "estimated_delay_risk": round(max_delay, 2),
            }
        if max_delay > 21 or critical:
            return {
                "strategy": "SEPARATE_SHIPMENT",
                "reason": "Un retard fournisseur peut bloquer le container ou le chantier.",
                "risk_level": "HIGH" if critical else "MEDIUM",
                "estimated_delay_risk": round(max_delay, 2),
            }
        return {
            "strategy": "GROUPED_WITH_BUFFER",
            "reason": "Groupage possible avec marge planning.",
            "risk_level": "MEDIUM",
            "estimated_delay_risk": round(max_delay, 2),
        }

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
