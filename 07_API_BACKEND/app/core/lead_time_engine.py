from __future__ import annotations

from typing import Any

from app.core.procurement_parameters import (
    DEFAULT_CONGO_CUSTOMS_DAYS,
    DEFAULT_LOCAL_TRANSPORT_DAYS,
    DEFAULT_SEA_FREIGHT_DAYS_CHINA_TO_POINTE_NOIRE,
    DEFAULT_SECURITY_BUFFER_DAYS,
    DEFAULT_SUPPLIER_PRODUCTION_DAYS,
)


class LeadTimeEngine:
    """Calcule un delai import complet Chine -> Pointe-Noire."""

    def evaluate(self, ligne: dict[str, Any]) -> dict[str, Any]:
        production = self._number(ligne.get("supplier_production_days"), DEFAULT_SUPPLIER_PRODUCTION_DAYS)
        maritime = self._number(
            ligne.get("sea_freight_days"),
            DEFAULT_SEA_FREIGHT_DAYS_CHINA_TO_POINTE_NOIRE,
        )
        customs = self._number(ligne.get("customs_days"), DEFAULT_CONGO_CUSTOMS_DAYS)
        local = self._number(ligne.get("local_transport_days"), DEFAULT_LOCAL_TRANSPORT_DAYS)
        buffer = self._number(ligne.get("security_buffer_days"), DEFAULT_SECURITY_BUFFER_DAYS)
        total = production + maritime + customs + local + buffer

        return {
            "total_import_lead_time": round(total, 2),
            "lead_time_level": self._level(total),
            "supplier_production_days": production,
            "sea_freight_days": maritime,
            "customs_days": customs,
            "local_transport_days": local,
            "security_buffer_days": buffer,
            "comment": "Delai total = production + maritime + douane + transport local + marge securite.",
        }

    def _level(self, total: float) -> str:
        if total <= 45:
            return "LOW"
        if total <= 75:
            return "MEDIUM"
        if total <= 100:
            return "HIGH"
        return "CRITICAL"

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
