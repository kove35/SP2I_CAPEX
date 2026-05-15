from __future__ import annotations

from typing import Any

from app.core.consolidation_engine import ConsolidationEngine
from app.core.container_engine import ContainerEngine
from app.core.freight_engine import FreightEngine
from app.core.shipment_engine import ShipmentEngine
from app.core.site_logistics_engine import SiteLogisticsEngine


class LogisticsEngine:
    """Orchestre container, fret, shipment et livraison chantier."""

    def __init__(self) -> None:
        self.container_engine = ContainerEngine()
        self.consolidation_engine = ConsolidationEngine()
        self.freight_engine = FreightEngine()
        self.shipment_engine = ShipmentEngine()
        self.site_logistics_engine = SiteLogisticsEngine()

    def evaluate_line(self, ligne: dict[str, Any]) -> dict[str, Any]:
        container = self.container_engine.evaluate(ligne)
        consolidation = self.consolidation_engine.evaluate([ligne])
        freight = self.freight_engine.evaluate(ligne, container)
        lead_time = self._number(ligne.get("TOTAL_IMPORT_LEAD_TIME") or ligne.get("lead_time_days"), 80)
        shipment = self.shipment_engine.evaluate(ligne, lead_time)
        site = self.site_logistics_engine.evaluate(ligne, container, shipment)

        return {
            "container_plan": container,
            "consolidation_analysis": consolidation,
            "freight_analysis": freight,
            "shipment_analysis": shipment,
            "site_delivery_analysis": site,
            "recommendation": self._recommendation(container, consolidation, freight, shipment, site),
        }

    def enrich_line(self, ligne: dict[str, Any]) -> dict[str, Any]:
        analysis = self.evaluate_line(ligne)
        container = analysis["container_plan"]
        consolidation = analysis["consolidation_analysis"]
        freight = analysis["freight_analysis"]
        shipment = analysis["shipment_analysis"]
        site = analysis["site_delivery_analysis"]

        return {
            **ligne,
            "LOGISTICS_ANALYSIS": analysis,
            "CONTAINER_STRATEGY": container["shipment_mode"],
            "SHIPMENT_STRATEGY": consolidation["strategy"],
            "FILL_RATE": container["fill_rate"],
            "SHIPMENT_COST": freight["total_logistics_cost"],
            "LEAD_TIME_TOTAL": shipment["lead_time_total"],
            "STORAGE_COST": site["storage_cost"],
            "DELIVERY_RISK": site["delivery_risk"],
            "CONTAINER_TYPE": container["container_type"],
            "CONTAINERS_REQUIRED": container["containers_required"],
        }

    def _recommendation(
        self,
        container: dict[str, Any],
        consolidation: dict[str, Any],
        freight: dict[str, Any],
        shipment: dict[str, Any],
        site: dict[str, Any],
    ) -> str:
        alerts = []
        if container["fill_rate"] < 0.35:
            alerts.append("remplissage faible, LCL ou groupage a privilegier")
        if consolidation["risk_level"] in {"HIGH", "CRITICAL"}:
            alerts.append("groupage risquant de bloquer le planning")
        if shipment["delay_risk"] in {"HIGH", "CRITICAL"}:
            alerts.append("ETA chantier a risque")
        if site["delivery_risk"] == "HIGH":
            alerts.append("stockage ou livraison chantier a securiser")
        if not alerts:
            return "Plan logistique coherent pour import Pointe-Noire."
        return "Surveillance logistique requise : " + ", ".join(alerts) + "."

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
