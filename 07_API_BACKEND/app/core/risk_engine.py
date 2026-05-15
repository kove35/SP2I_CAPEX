from __future__ import annotations

from typing import Any

from app.core.procurement_parameters import CRITICALITY_RISK, DEFAULT_COUNTRY_RISKS, RISK_WEIGHTS


class RiskEngine:
    """
    Score les risques d'import de maniere explicable.

    Le score final est une combinaison de quatre familles de risques :
    fournisseur, pays, logistique et chantier.
    """

    def evaluate(self, ligne: dict[str, Any]) -> dict[str, Any]:
        supplier_risk = self._supplier_risk(ligne)
        country_risk = self._country_risk(ligne)
        logistics_risk = self._logistics_risk(ligne)
        project_risk = self._project_risk(ligne)

        global_risk = (
            supplier_risk * RISK_WEIGHTS["supplier"]
            + country_risk * RISK_WEIGHTS["country"]
            + logistics_risk * RISK_WEIGHTS["logistics"]
            + project_risk * RISK_WEIGHTS["project"]
        )

        return {
            "global_risk_score": round(global_risk, 2),
            "risk_level": self._risk_level(global_risk),
            "supplier_risk": round(supplier_risk, 2),
            "country_risk": round(country_risk, 2),
            "logistics_risk": round(logistics_risk, 2),
            "project_risk": round(project_risk, 2),
            "reasoning": {
                "weights": RISK_WEIGHTS,
                "comments": [
                    "Risque fournisseur base sur fiabilite, qualite et retards.",
                    "Risque pays base sur douane, port, change et contexte politique.",
                    "Risque logistique base sur port, maritime et transport local.",
                    "Risque chantier base sur criticite et impact retard.",
                ],
            },
        }

    def _supplier_risk(self, ligne: dict[str, Any]) -> float:
        reliability = self._number(ligne.get("reliability_score"), 70)
        quality = self._number(ligne.get("quality_score"), 70)
        delay = self._number(ligne.get("supplier_delay_risk"), 35)
        return max(0, min(((100 - reliability) * 0.45) + ((100 - quality) * 0.30) + (delay * 0.25), 100))

    def _country_risk(self, ligne: dict[str, Any]) -> float:
        customs = self._number(ligne.get("customs_risk"), DEFAULT_COUNTRY_RISKS["customs_risk"])
        currency = self._number(ligne.get("currency_risk"), DEFAULT_COUNTRY_RISKS["currency_risk"])
        political = self._number(ligne.get("political_risk"), DEFAULT_COUNTRY_RISKS["political_risk"])
        return max(0, min((customs * 0.45) + (currency * 0.25) + (political * 0.30), 100))

    def _logistics_risk(self, ligne: dict[str, Any]) -> float:
        port = self._number(ligne.get("port_risk"), DEFAULT_COUNTRY_RISKS["port_risk"])
        logistics = self._number(ligne.get("logistics_risk"), DEFAULT_COUNTRY_RISKS["logistics_risk"])
        lead_time = self._number(ligne.get("lead_time_days"), 80)
        delay_pressure = min(lead_time / 100 * 100, 100)
        return max(0, min((port * 0.35) + (logistics * 0.35) + (delay_pressure * 0.30), 100))

    def _project_risk(self, ligne: dict[str, Any]) -> float:
        criticality = str(ligne.get("project_criticality") or "MEDIUM").upper()
        return float(CRITICALITY_RISK.get(criticality, CRITICALITY_RISK["MEDIUM"]))

    def _risk_level(self, score: float) -> str:
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
