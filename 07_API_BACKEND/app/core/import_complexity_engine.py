from __future__ import annotations

from typing import Any

from app.core.procurement_parameters import PRODUCT_COMPLEXITY_DEFAULTS


class ImportComplexityEngine:
    """Evalue la complexite physique et reglementaire d'un import."""

    def evaluate(self, ligne: dict[str, Any]) -> dict[str, Any]:
        designation = str(ligne.get("designation") or "").lower()
        famille = str(ligne.get("famille") or "").lower()
        base = self._default_complexity(designation, famille)
        weight = self._number(ligne.get("weight_risk"), 0)
        volume = self._number(ligne.get("volume_risk"), 0)
        fragility = self._number(ligne.get("fragility_risk"), 0)
        certification = self._number(ligne.get("certification_risk"), 0)
        installation = self._number(ligne.get("installation_risk"), 0)
        after_sales = self._number(ligne.get("after_sales_risk"), 0)
        customs = self._number(ligne.get("specific_customs_risk"), 0)

        score = min(
            base
            + weight * 0.10
            + volume * 0.10
            + fragility * 0.15
            + certification * 0.20
            + installation * 0.20
            + after_sales * 0.15
            + customs * 0.10,
            100,
        )

        return {
            "complexity_score": round(score, 2),
            "complexity_level": self._level(score),
            "requires_special_handling": score >= 70,
            "comment": "Complexite basee sur produit, manutention, certification, installation et SAV.",
        }

    def _default_complexity(self, designation: str, famille: str) -> float:
        source = f"{designation} {famille}"
        for keyword, score in PRODUCT_COMPLEXITY_DEFAULTS.items():
            if keyword in source:
                return float(score)
        return 45.0

    def _level(self, score: float) -> str:
        if score < 30:
            return "LOW"
        if score < 60:
            return "MEDIUM"
        if score < 80:
            return "HIGH"
        return "CRITICAL"

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
