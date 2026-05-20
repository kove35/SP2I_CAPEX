from __future__ import annotations

from typing import Any

from app.core.price_reference_repository import PriceReferenceRepository


class FinancialReferenceEngine:
    """Expose les ranges financiers CAPEX par equipement, region et qualite."""

    REGION_FACTORS = {
        "CONGO_BRAZZAVILLE": 1.08,
        "CENTRAL_AFRICA": 1.0,
        "WEST_AFRICA": 0.95,
        "IMPORT_CHINA": 0.72,
    }
    QUALITY_FACTORS = {
        "LOW_COST": 0.72,
        "MEDIUM": 1.0,
        "PREMIUM": 1.45,
    }

    def __init__(self, repository: PriceReferenceRepository | None = None) -> None:
        self.repository = repository or PriceReferenceRepository()

    def get_reference(
        self,
        equipment_type: str | None,
        region: str = "CENTRAL_AFRICA",
        quality: str = "MEDIUM",
    ) -> dict[str, Any]:
        base = self.repository.get_equipment_reference(equipment_type)
        if not base:
            return {}
        region = region.upper()
        quality = quality.upper()
        factor = self.REGION_FACTORS.get(region, 1.0) * self.QUALITY_FACTORS.get(quality, 1.0)
        return {
            **base,
            "equipment_type": equipment_type,
            "price_min": round(float(base["price_min"]) * factor, 2),
            "price_max": round(float(base["price_max"]) * factor, 2),
            "currency": base.get("currency", "FCFA"),
            "quality": quality,
            "region": region,
            "source": "SP2I_CAPEX_KNOWLEDGE_ENGINE_V1",
        }

    def benchmark_price(self, equipment_type: str | None, price: float, region: str = "CENTRAL_AFRICA") -> dict[str, Any]:
        reference = self.get_reference(equipment_type, region=region)
        if not reference:
            return {"status": "UNKNOWN_REFERENCE", "financial_confidence_score": 25.0}
        price_min = float(reference["price_min"])
        price_max = float(reference["price_max"])
        midpoint = (price_min + price_max) / 2
        if price_min <= price <= price_max:
            status = "IN_RANGE"
            confidence = 95.0
        else:
            spread = max(price_max - price_min, 1.0)
            distance = abs(price - midpoint) / spread
            status = "BELOW_RANGE" if price < price_min else "ABOVE_RANGE"
            confidence = max(10.0, 75.0 - distance * 50.0)
        return {
            "status": status,
            "reference": reference,
            "financial_confidence_score": round(confidence, 2),
        }
