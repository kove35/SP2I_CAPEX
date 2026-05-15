from __future__ import annotations

from typing import Any

from app.core.decision_parameters import (
    CRITICALITY_WEIGHTS,
    DECISION_RULES,
    DEFAULT_CRITICALITY,
    DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_LOGISTICS_RISK_SCORE,
    DEFAULT_SUPPLIER_RISK_SCORE,
    HIGH_CONFIDENCE_SCORE,
    MEDIUM_CONFIDENCE_SCORE,
    MIN_IMPORT_SCORE,
    MIN_MIXED_SCORE,
    WEIGHT_CRITICALITY,
    WEIGHT_LEAD_TIME,
    WEIGHT_RISK,
    WEIGHT_SAVINGS,
)


class DecisionEngine:
    """
    Moteur decisionnel explicable pour l'arbitrage import/local.

    Le moteur ne remplace pas `CalculateurCAPEX`. Il prend ses resultats
    financiers, ajoute les notions risque/delai/criticite, puis produit une
    decision argumentee et historisable.
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        parameters = parameters or {}
        self.weights = {
            "savings": float(parameters.get("weight_savings", WEIGHT_SAVINGS)),
            "risk": float(parameters.get("weight_risk", WEIGHT_RISK)),
            "lead_time": float(parameters.get("weight_lead_time", WEIGHT_LEAD_TIME)),
            "criticality": float(parameters.get("weight_criticality", WEIGHT_CRITICALITY)),
        }
        self.min_import_score = float(parameters.get("min_import_score", MIN_IMPORT_SCORE))
        self.min_mixed_score = float(parameters.get("min_mixed_score", MIN_MIXED_SCORE))

    def evaluate_savings(self, ligne: dict[str, Any]) -> dict[str, Any]:
        capex_local = self._nombre(ligne.get("CAPEX_LOCAL") or ligne.get("capex_local"))
        economie = self._nombre(ligne.get("ECONOMIE_NETTE") or ligne.get("economie"))
        taux = economie / capex_local if capex_local else 0

        # 25% d'economie ou plus est considere comme un excellent signal.
        score = max(0, min(taux / 0.25 * 100, 100))
        return {
            "score": round(score, 2),
            "taux_economie": round(taux, 4),
            "comment": f"Economie estimee {round(taux * 100, 2)}%.",
        }

    def evaluate_risk(self, ligne: dict[str, Any]) -> dict[str, Any]:
        supplier_risk = self._nombre(ligne.get("supplier_risk_score"), DEFAULT_SUPPLIER_RISK_SCORE)
        logistics_risk = self._nombre(ligne.get("logistics_risk_score"), DEFAULT_LOGISTICS_RISK_SCORE)
        import_risk = (supplier_risk * 0.55) + (logistics_risk * 0.45)

        # Plus le risque est eleve, plus le score positif baisse.
        score = max(0, 100 - import_risk)
        return {
            "score": round(score, 2),
            "risk_score": round(import_risk, 2),
            "supplier_risk": round(supplier_risk, 2),
            "logistics_risk": round(logistics_risk, 2),
            "comment": f"Risque combine fournisseur/logistique {round(import_risk, 2)}/100.",
        }

    def evaluate_lead_time(self, ligne: dict[str, Any]) -> dict[str, Any]:
        lead_time_days = self._nombre(ligne.get("lead_time_days"), DEFAULT_LEAD_TIME_DAYS)

        # 0 jour = excellent, 90 jours ou plus = tres penalisant.
        score = max(0, 100 - (lead_time_days / 90 * 100))
        return {
            "score": round(score, 2),
            "lead_time_days": round(lead_time_days, 2),
            "comment": f"Delai estime {round(lead_time_days, 1)} jours.",
        }

    def evaluate_project_criticality(self, ligne: dict[str, Any]) -> dict[str, Any]:
        criticality = str(ligne.get("project_criticality") or DEFAULT_CRITICALITY).upper()
        penalty = CRITICALITY_WEIGHTS.get(criticality, CRITICALITY_WEIGHTS[DEFAULT_CRITICALITY])

        # Une criticite forte penalise l'import car le planning chantier tolere
        # moins les aleas fournisseur/logistique.
        score = max(0, 100 - penalty)
        return {
            "score": round(score, 2),
            "criticality": criticality,
            "criticality_penalty": penalty,
            "comment": f"Criticite chantier {criticality}.",
        }

    def make_decision(self, ligne: dict[str, Any]) -> dict[str, Any]:
        savings = self.evaluate_savings(ligne)
        risk = self.evaluate_risk(ligne)
        lead_time = self.evaluate_lead_time(ligne)
        criticality = self.evaluate_project_criticality(ligne)

        final_score = (
            savings["score"] * self.weights["savings"]
            + risk["score"] * self.weights["risk"]
            + lead_time["score"] * self.weights["lead_time"]
            + criticality["score"] * self.weights["criticality"]
        )
        final_score = round(final_score, 2)

        if final_score >= self.min_import_score:
            decision = "IMPORT"
            decision_type = "IMPORT_AGRESSIF" if savings["score"] >= 70 else "IMPORT_CONTROLE"
        elif final_score >= self.min_mixed_score:
            decision = "MIXTE"
            decision_type = "MIXTE_OPTIMISE"
        else:
            decision = "LOCAL"
            decision_type = "LOCAL_SECURISE"

        confidence = self._confidence(final_score)
        return {
            "decision": decision,
            "decision_type": decision_type,
            "final_score": final_score,
            "confidence": confidence,
            "reasoning": {
                "savings_score": savings["score"],
                "risk_score": risk["risk_score"],
                "risk_positive_score": risk["score"],
                "lead_time_score": lead_time["score"],
                "criticality_score": criticality["score"],
                "weights": self.weights,
                "comments": [
                    savings["comment"],
                    risk["comment"],
                    lead_time["comment"],
                    criticality["comment"],
                    DECISION_RULES[decision],
                ],
            },
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
            "RISK_SCORE": decision["reasoning"]["risk_score"],
            "LEAD_TIME_SCORE": decision["reasoning"]["lead_time_score"],
            "CRITICALITY_SCORE": decision["reasoning"]["criticality_score"],
        }

    def _confidence(self, final_score: float) -> str:
        if final_score >= HIGH_CONFIDENCE_SCORE:
            return "HIGH"
        if final_score >= MEDIUM_CONFIDENCE_SCORE:
            return "MEDIUM"
        return "LOW"

    def _nombre(self, valeur: Any, default: float = 0) -> float:
        try:
            return float(valeur if valeur is not None else default)
        except (TypeError, ValueError):
            return default
