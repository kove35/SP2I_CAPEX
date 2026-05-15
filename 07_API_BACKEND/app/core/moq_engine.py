from __future__ import annotations

from typing import Any


class MOQEngine:
    """Analyse les Minimum Order Quantity fournisseur."""

    def evaluate(self, ligne: dict[str, Any]) -> dict[str, Any]:
        required = self._number(ligne.get("QTE") or ligne.get("quantite"), 0)
        moq = self._number(ligne.get("supplier_moq") or ligne.get("minimum_order_quantity"), required)
        surplus = max(moq - required, 0)
        moq_respected = required >= moq
        surplus_ratio = surplus / required if required else 0
        risk = min(surplus_ratio * 100, 100) if not moq_respected else 0

        return {
            "moq_respected": moq_respected,
            "required_quantity": round(required, 2),
            "supplier_moq": round(moq, 2),
            "surplus_quantity": round(surplus, 2),
            "moq_risk_score": round(risk, 2),
            "comment": "MOQ non respecte = risque de sur-stock et faux gain economique.",
        }

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
