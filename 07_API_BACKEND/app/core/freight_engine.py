from __future__ import annotations

from typing import Any

from app.core.logistics_parameters import (
    DEFAULT_CUSTOMS_RATE,
    DEFAULT_INSURANCE_RATE,
    DEFAULT_LOCAL_DELIVERY_RATE,
    DEFAULT_PORT_COST_RATE,
    DEFAULT_STORAGE_COST_PER_CBM_DAY,
    DEFAULT_SITE_STORAGE_DAYS,
)


class FreightEngine:
    """Calcule les couts logistiques d'import jusqu'au chantier."""

    def evaluate(self, ligne: dict[str, Any], container_plan: dict[str, Any]) -> dict[str, Any]:
        capex_import = self._number(ligne.get("CAPEX_IMPORT") or ligne.get("capex_import"), 0)
        freight_cost = self._number(ligne.get("freight_cost"), container_plan.get("container_cost", 0))
        customs_cost = capex_import * self._number(ligne.get("customs_rate"), DEFAULT_CUSTOMS_RATE)
        insurance_cost = capex_import * self._number(ligne.get("insurance_rate"), DEFAULT_INSURANCE_RATE)
        port_cost = freight_cost * self._number(ligne.get("port_cost_rate"), DEFAULT_PORT_COST_RATE)
        local_delivery_cost = capex_import * self._number(
            ligne.get("local_delivery_rate"),
            DEFAULT_LOCAL_DELIVERY_RATE,
        )
        storage_cost = (
            self._number(container_plan.get("volume_total"), 0)
            * self._number(ligne.get("storage_days"), DEFAULT_SITE_STORAGE_DAYS)
            * DEFAULT_STORAGE_COST_PER_CBM_DAY
        )
        total = freight_cost + customs_cost + insurance_cost + port_cost + local_delivery_cost + storage_cost

        return {
            "freight_cost": round(freight_cost, 2),
            "customs_cost": round(customs_cost, 2),
            "insurance_cost": round(insurance_cost, 2),
            "port_cost": round(port_cost, 2),
            "local_delivery_cost": round(local_delivery_cost, 2),
            "storage_cost": round(storage_cost, 2),
            "total_logistics_cost": round(total, 2),
            "comment": "Cout total = maritime + port + douane + assurance + livraison + stockage.",
        }

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
