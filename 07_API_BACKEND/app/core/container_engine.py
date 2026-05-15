from __future__ import annotations

import math
from typing import Any

from app.core.logistics_parameters import CONTAINERS, FCL_FILL_RATE_THRESHOLD, LCL_COST_PER_CBM


class ContainerEngine:
    """Calcule le plan container a partir du volume et du poids."""

    def evaluate(self, ligne: dict[str, Any]) -> dict[str, Any]:
        quantity = self._number(ligne.get("QTE") or ligne.get("quantite"), 0)
        unit_volume = self._number(ligne.get("volume_unitaire_m3"), 0.03)
        unit_weight = self._number(ligne.get("poids_unitaire_kg"), 5)
        total_volume = quantity * unit_volume
        total_weight = quantity * unit_weight

        container_type = self._choose_container(total_volume, total_weight)
        specs = CONTAINERS[container_type]
        containers_required = max(
            1,
            math.ceil(max(total_volume / specs["max_volume"], total_weight / specs["max_weight"])),
        )
        capacity = specs["max_volume"] * containers_required
        fill_rate = total_volume / capacity if capacity else 0
        shipment_mode = "FCL" if fill_rate >= FCL_FILL_RATE_THRESHOLD or containers_required > 1 else "LCL"
        estimated_cost = (
            containers_required * specs["container_cost"]
            if shipment_mode == "FCL"
            else max(total_volume, 1) * LCL_COST_PER_CBM
        )

        return {
            "container_type": container_type,
            "containers_required": containers_required,
            "shipment_mode": shipment_mode,
            "fill_rate": round(fill_rate, 4),
            "volume_total": round(total_volume, 2),
            "weight_total": round(total_weight, 2),
            "remaining_capacity": round(max(capacity - total_volume, 0), 2),
            "cost_per_m3": round(estimated_cost / max(total_volume, 1), 2),
            "container_cost": round(estimated_cost, 2),
            "comment": "FCL si le remplissage est suffisant, sinon LCL/groupage conseille.",
        }

    def _choose_container(self, volume: float, weight: float) -> str:
        if volume <= CONTAINERS["20FT"]["max_volume"] and weight <= CONTAINERS["20FT"]["max_weight"]:
            return "20FT"
        if volume <= CONTAINERS["40FT"]["max_volume"] and weight <= CONTAINERS["40FT"]["max_weight"]:
            return "40FT"
        return "40HC"

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
