from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.core.logistics_parameters import SHIPMENT_STATUS_DAYS_REMAINING


class ShipmentEngine:
    """Suit le flux logistique usine -> chantier."""

    def evaluate(self, ligne: dict[str, Any], lead_time_days: float) -> dict[str, Any]:
        status = str(ligne.get("shipment_status") or "READY").upper()
        eta_days = self._number(ligne.get("eta_days"), SHIPMENT_STATUS_DAYS_REMAINING.get(status, lead_time_days))
        requested_days = self._number(ligne.get("required_on_site_days"), lead_time_days + 10)
        delay = max(eta_days - requested_days, 0)
        delivery_date = date.today() + timedelta(days=int(round(eta_days)))

        return {
            "shipment_status": status,
            "eta_days": round(eta_days, 2),
            "lead_time_total": round(lead_time_days, 2),
            "estimated_site_delivery": delivery_date.isoformat(),
            "delay_days": round(delay, 2),
            "delay_risk": self._delay_risk(delay, eta_days),
            "comment": "ETA calcule depuis le statut logistique et le delai restant.",
        }

    def _delay_risk(self, delay: float, eta_days: float) -> str:
        if delay > 21 or eta_days > 100:
            return "CRITICAL"
        if delay > 7 or eta_days > 75:
            return "HIGH"
        if delay > 0 or eta_days > 45:
            return "MEDIUM"
        return "LOW"

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
