from __future__ import annotations

from typing import Any

from app.core.calculator import CalculateurCAPEX
from app.core.kpi_engine import KPIEngine


SCENARIO_PROFILES: list[dict[str, Any]] = [
    {
        "code": "CONSERVATEUR",
        "label": "Conservateur",
        "description": "Seuil de decision strict, priorite risque et delai.",
        "weight_savings": 0.25,
        "weight_risk": 0.30,
        "weight_lead_time": 0.25,
        "weight_criticality": 0.10,
        "weight_importability": 0.05,
        "weight_procurement_maturity": 0.05,
    },
    {
        "code": "EQUILIBRE",
        "label": "Equilibre",
        "description": "Arbitrage standard entre gains et risques.",
        "weight_savings": 0.30,
        "weight_risk": 0.25,
        "weight_lead_time": 0.20,
        "weight_criticality": 0.10,
        "weight_importability": 0.10,
        "weight_procurement_maturity": 0.05,
    },
    {
        "code": "AGRESSIF",
        "label": "Agressif",
        "description": "Favorise le potentiel economique en acceptant plus de risques. ",
        "weight_savings": 0.40,
        "weight_risk": 0.20,
        "weight_lead_time": 0.15,
        "weight_criticality": 0.10,
        "weight_importability": 0.10,
        "weight_procurement_maturity": 0.05,
    },
]


class ScenarioEngine:
    """Moteur de generation de scenarios procurement et landed cost."""

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        self.parameters = parameters or {}
        self.kpi_engine = KPIEngine()

    def definition(self) -> list[dict[str, Any]]:
        return SCENARIO_PROFILES.copy()

    def analyse_landed_cost_variations(self, lignes: list[dict[str, Any]], variations: list[float]) -> list[dict[str, Any]]:
        scenarios: list[dict[str, Any]] = []
        for variation in variations:
            parametres = {
                "taux_landed_cost": {
                    nom: float(taux) * (1 + variation)
                    for nom, taux in self.parameters.get("taux_landed_cost", {}).items()
                }
            }
            calculateur = CalculateurCAPEX({**self.parameters, **parametres})
            lignes_scenario = calculateur.optimiser_lignes(lignes)
            kpi = calculateur.calculer_kpi(lignes_scenario)
            scenarios.append(
                {
                    "variation": variation,
                    "scenario_type": "LANDED_COST",
                    "label": f"Landed cost {round(variation * 100)}%",
                    "kpi": kpi,
                }
            )
        return scenarios

    def evaluate_scenarios(self, lignes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scenarios: list[dict[str, Any]] = []
        for profile in SCENARIO_PROFILES:
            scenarios.append(
                {
                    "code": profile["code"],
                    "label": profile["label"],
                    "description": profile["description"],
                    "weights": {
                        key: profile[key] for key in profile if key.startswith("weight_")
                    },
                }
            )
        return scenarios
