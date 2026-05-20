from __future__ import annotations

from typing import Any

from app.core.decision_engine import DecisionEngine
from app.core.decision_parameters import DECISION_RULES


SCENARIO_PROFILES: dict[str, dict[str, float]] = {
    "CONSERVATEUR": {
        "weight_savings": 0.25,
        "weight_risk": 0.30,
        "weight_lead_time": 0.25,
        "weight_criticality": 0.10,
        "weight_importability": 0.05,
        "weight_procurement_maturity": 0.05,
        "min_import_score": 75,
        "min_mixed_score": 60,
    },
    "EQUILIBRE": {
        "weight_savings": 0.30,
        "weight_risk": 0.25,
        "weight_lead_time": 0.20,
        "weight_criticality": 0.10,
        "weight_importability": 0.10,
        "weight_procurement_maturity": 0.05,
        "min_import_score": 70,
        "min_mixed_score": 50,
    },
    "AGRESSIF": {
        "weight_savings": 0.40,
        "weight_risk": 0.20,
        "weight_lead_time": 0.15,
        "weight_criticality": 0.10,
        "weight_importability": 0.10,
        "weight_procurement_maturity": 0.05,
        "min_import_score": 60,
        "min_mixed_score": 45,
    },
    "BASELINE": {
        "weight_savings": 0.35,
        "weight_risk": 0.25,
        "weight_lead_time": 0.20,
        "weight_criticality": 0.10,
        "weight_importability": 0.05,
        "weight_procurement_maturity": 0.05,
        "min_import_score": 65,
        "min_mixed_score": 45,
    },
}


class DecisionEngineV2(DecisionEngine):
    """Decision engine enterprise pour import/local avec profils de scenarios."""

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        parameters = parameters or {}
        self.scenario_type = str(parameters.get("scenario_type", "BASELINE")).upper()
        self.profile = SCENARIO_PROFILES.get(self.scenario_type, SCENARIO_PROFILES["BASELINE"])
        super().__init__(parameters)

    def make_decision(self, ligne: dict[str, Any]) -> dict[str, Any]:
        savings = self.evaluate_savings(ligne)
        risk = self.evaluate_risk(ligne)
        lead_time = self.evaluate_lead_time(ligne)
        criticality = self.evaluate_project_criticality(ligne)
        importability = self._evaluate_importability(ligne)
        procurement_maturity = self._evaluate_procurement_maturity(ligne)

        final_score = (
            savings["score"] * self.profile["weight_savings"]
            + risk["score"] * self.profile["weight_risk"]
            + lead_time["score"] * self.profile["weight_lead_time"]
            + criticality["score"] * self.profile["weight_criticality"]
            + importability["score"] * self.profile["weight_importability"]
            + procurement_maturity["score"] * self.profile["weight_procurement_maturity"]
        )
        final_score = round(final_score, 2)

        if final_score >= self.profile["min_import_score"]:
            decision = "IMPORT"
            decision_type = "IMPORT_AGRESSIF" if savings["score"] >= 70 else "IMPORT_CONTROLE"
        elif final_score >= self.profile["min_mixed_score"]:
            decision = "MIXTE"
            decision_type = "MIXTE_OPTIMISE"
        else:
            decision = "LOCAL"
            decision_type = "LOCAL_SECURISE"

        confidence = self._confidence(final_score)
        reasoning = {
            "savings_score": savings["score"],
            "risk_score": risk["risk_score"],
            "risk_positive_score": risk["score"],
            "lead_time_score": lead_time["score"],
            "criticality_score": criticality["score"],
            "importability_score": importability["score"],
            "procurement_maturity_score": procurement_maturity["score"],
            "weights": self.profile,
            "comments": [
                savings["comment"],
                risk["comment"],
                lead_time["comment"],
                criticality["comment"],
                importability["comment"],
                procurement_maturity["comment"],
                DECISION_RULES[decision],
            ],
        }

        return {
            "decision": decision,
            "decision_type": decision_type,
            "final_score": final_score,
            "confidence": confidence,
            "reasoning": reasoning,
            "scenario_type": self.scenario_type,
        }

    def enrich_line(self, ligne: dict[str, Any]) -> dict[str, Any]:
        decision = self.make_decision(ligne)
        return {
            **ligne,
            "DECISION_FINALE": decision["decision"],
            "DECISION_TYPE": decision["decision_type"],
            "FINAL_DECISION_SCORE": decision["final_score"],
            "DECISION_CONFIDENCE": decision["confidence"],
            "DECISION_REASON": decision["reasoning"],
            "DECISION_SCENARIO": decision["scenario_type"],
        }

    def _evaluate_importability(self, ligne: dict[str, Any]) -> dict[str, Any]:
        score = self._nombre(ligne.get("IMPORTABILITY_SCORE"), 50)
        comment = "Importabilite calculee sur les signaux procurement et logistiques."
        if score >= 70:
            comment = "Importabilite elevee, ligne bien couverte pour import."
        elif score >= 45:
            comment = "Importabilite moyenne, verifier disponibilite et delai."
        else:
            comment = "Importabilite faible, attention aux risques ou donnees manquantes."
        return {"score": round(min(max(score, 0), 100), 2), "comment": comment}

    def _evaluate_procurement_maturity(self, ligne: dict[str, Any]) -> dict[str, Any]:
        score = self._nombre(ligne.get("PROCUREMENT_MATURITY_SCORE"), 50)
        return {
            "score": round(min(max(score, 0), 100), 2),
            "comment": "Maturite procurement mesuree sur la couverture et la qualite des donnees import."
        }
