from __future__ import annotations

from typing import Any

from app.core.procurement_parameters import DEFAULT_ADVANCE_PAYMENT_RATE, DEFAULT_REMAINING_PAYMENT_RATE


class CashflowEngine:
    """Mesure l'impact tresorerie d'un achat import."""

    def evaluate(self, ligne: dict[str, Any]) -> dict[str, Any]:
        capex_import = self._number(ligne.get("CAPEX_IMPORT") or ligne.get("capex_import"), 0)
        advance_rate = self._number(ligne.get("advance_payment_rate"), DEFAULT_ADVANCE_PAYMENT_RATE)
        remaining_rate = self._number(ligne.get("remaining_payment_rate"), DEFAULT_REMAINING_PAYMENT_RATE)
        cashflow_tension = str(ligne.get("cashflow_tension") or "MEDIUM").upper()

        advance = capex_import * advance_rate
        remaining = capex_import * remaining_rate
        exposure = advance + remaining
        tension_penalty = {"LOW": 10, "MEDIUM": 35, "HIGH": 70, "CRITICAL": 90}.get(cashflow_tension, 35)
        score = max(0, 100 - min((exposure / max(capex_import, 1) * 20) + tension_penalty, 100))

        return {
            "cashflow_score": round(score, 2),
            "cashflow_risk": self._risk(score),
            "advance_payment": round(advance, 2),
            "remaining_payment": round(remaining, 2),
            "cashflow_tension": cashflow_tension,
            "comment": "Score bas = tresorerie plus exposee avant livraison chantier.",
        }

    def _risk(self, score: float) -> str:
        if score >= 70:
            return "LOW"
        if score >= 45:
            return "MEDIUM"
        if score >= 25:
            return "HIGH"
        return "CRITICAL"

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
