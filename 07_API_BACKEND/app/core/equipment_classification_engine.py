from __future__ import annotations

from typing import Any

from app.core.capex_taxonomy_engine import CAPEXTaxonomyEngine
from app.core.financial_reference_engine import FinancialReferenceEngine


class EquipmentClassificationEngine:
    """Orchestre taxonomie, normalisation et references financieres."""

    def __init__(
        self,
        taxonomy_engine: CAPEXTaxonomyEngine | None = None,
        financial_engine: FinancialReferenceEngine | None = None,
    ) -> None:
        self.taxonomy_engine = taxonomy_engine or CAPEXTaxonomyEngine()
        self.financial_engine = financial_engine or FinancialReferenceEngine()

    def classify_line(self, line: dict[str, Any]) -> dict[str, Any]:
        classification = self.taxonomy_engine.classify(str(line.get("designation", "")))
        reference = self.financial_engine.get_reference(
            classification.get("equipment_type"),
            region=str(line.get("region", "CENTRAL_AFRICA")),
            quality=str(line.get("quality", "MEDIUM")),
        )
        return {
            **classification,
            "financial_reference": reference,
            "procurement_confidence_score": self._procurement_confidence(classification, reference),
        }

    def _procurement_confidence(self, classification: dict[str, Any], reference: dict[str, Any]) -> float:
        score = 35.0
        if classification.get("family") != "UNKNOWN":
            score += 30.0
        score += min(float(classification.get("semantic_confidence_score", 0)) * 0.2, 20.0)
        if reference:
            score += 15.0
        return round(min(score, 100.0), 2)
