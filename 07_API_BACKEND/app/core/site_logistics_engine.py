from __future__ import annotations

from typing import Any

from app.core.logistics_parameters import DEFAULT_SITE_STORAGE_CAPACITY_CBM, DEFAULT_STORAGE_COST_PER_CBM_DAY


class SiteLogisticsEngine:
    """Analyse stockage chantier et risque de livraison."""

    def evaluate(self, ligne: dict[str, Any], container_plan: dict[str, Any], shipment: dict[str, Any]) -> dict[str, Any]:
        volume = self._number(container_plan.get("volume_total"), 0)
        capacity = self._number(ligne.get("site_storage_capacity_m3"), DEFAULT_SITE_STORAGE_CAPACITY_CBM)
        storage_days = self._number(ligne.get("storage_days"), 5)
        saturation = volume / capacity if capacity else 1
        storage_cost = volume * storage_days * DEFAULT_STORAGE_COST_PER_CBM_DAY
        delay_risk = shipment.get("delay_risk", "LOW")

        if saturation > 1 or delay_risk in {"HIGH", "CRITICAL"}:
            delivery_risk = "HIGH"
        elif saturation > 0.75 or delay_risk == "MEDIUM":
            delivery_risk = "MEDIUM"
        else:
            delivery_risk = "LOW"

        return {
            "storage_cost": round(storage_cost, 2),
            "site_saturation_rate": round(saturation, 4),
            "delivery_risk": delivery_risk,
            "delivery_priority": str(ligne.get("delivery_priority") or "NORMAL").upper(),
            "comment": "Livraison trop tot = stockage, trop tard = risque planning chantier.",
        }

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
