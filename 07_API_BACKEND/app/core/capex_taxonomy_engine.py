from __future__ import annotations

from typing import Any

from app.core.price_reference_repository import PriceReferenceRepository
from app.core.semantic_normalization_engine import SemanticNormalizationEngine


class CAPEXTaxonomyEngine:
    """Classifie une designation dans la taxonomie CAPEX enterprise."""

    def __init__(
        self,
        repository: PriceReferenceRepository | None = None,
        normalizer: SemanticNormalizationEngine | None = None,
    ) -> None:
        self.repository = repository or PriceReferenceRepository()
        self.normalizer = normalizer or SemanticNormalizationEngine()

    def classify(self, designation: str | None) -> dict[str, Any]:
        normalized = self.normalizer.normalize(designation)
        text = normalized["normalized_designation"]
        tokens = set(normalized["tokens"])
        best: dict[str, Any] = {}
        best_score = 0.0

        for family, payload in self.repository.load_taxonomy().items():
            for entry in payload.get("entries", []):
                score = self._score_entry(text, tokens, entry)
                if score > best_score:
                    best_score = score
                    best = {
                        "family": family,
                        "subcategory": entry.get("subcategory"),
                        "equipment_type": entry.get("equipment_type"),
                        "equipment_class": entry.get("equipment_class"),
                    }

        confidence = min(best_score, 100.0)
        if not best:
            best = {
                "family": "UNKNOWN",
                "subcategory": "UNKNOWN",
                "equipment_type": "UNKNOWN",
                "equipment_class": "NON_CLASSE",
            }

        return {
            **best,
            **normalized["attributes"],
            "semantic_confidence_score": round(confidence, 2),
            "normalization_confidence_score": normalized["normalization_confidence_score"],
            "normalized_designation": text,
        }

    def list_families(self) -> list[str]:
        return sorted(self.repository.load_taxonomy())

    def _score_entry(self, text: str, tokens: set[str], entry: dict[str, Any]) -> float:
        score = 0.0
        keywords = [str(item).lower() for item in entry.get("keywords", [])]
        synonyms = [str(item).lower() for item in entry.get("synonyms", [])]
        for keyword in keywords:
            if keyword in tokens or keyword in text:
                score += 22.0
        for synonym in synonyms:
            if synonym in text:
                score += 18.0
        equipment_type = str(entry.get("equipment_type", "")).lower().replace("_", " ")
        if equipment_type and equipment_type in text:
            score += 25.0
        return score
