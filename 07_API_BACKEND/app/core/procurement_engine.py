from __future__ import annotations

from typing import Any

from app.core.cashflow_engine import CashflowEngine
from app.core.import_complexity_engine import ImportComplexityEngine
from app.core.lead_time_engine import LeadTimeEngine
from app.core.moq_engine import MOQEngine
from app.core.risk_engine import RiskEngine


class ProcurementEngine:
    """
    Orchestrateur procurement.

    Il compose des moteurs specialises sans remplacer le moteur CAPEX. Sa
    mission est d'ajouter le contexte import realiste : risque, delai, cashflow,
    MOQ et complexite.
    """

    def __init__(self) -> None:
        self.lead_time_engine = LeadTimeEngine()
        self.risk_engine = RiskEngine()
        self.cashflow_engine = CashflowEngine()
        self.moq_engine = MOQEngine()
        self.complexity_engine = ImportComplexityEngine()

    def evaluate(self, ligne: dict[str, Any]) -> dict[str, Any]:
        lead_time = self.lead_time_engine.evaluate(ligne)
        line_with_lead_time = {**ligne, "lead_time_days": lead_time["total_import_lead_time"]}
        risk = self.risk_engine.evaluate(line_with_lead_time)
        cashflow = self.cashflow_engine.evaluate(ligne)
        moq = self.moq_engine.evaluate(ligne)
        complexity = self.complexity_engine.evaluate(ligne)

        recommendation = self._recommendation(risk, lead_time, cashflow, moq, complexity)
        final_score = self._final_procurement_score(risk, lead_time, cashflow, moq, complexity)

        return {
            "decision": recommendation["decision"],
            "final_score": final_score,
            "risk_analysis": risk,
            "lead_time_analysis": lead_time,
            "cashflow_analysis": cashflow,
            "moq_analysis": moq,
            "complexity_analysis": complexity,
            "recommendation": recommendation["message"],
        }

    def enrich_line(self, ligne: dict[str, Any]) -> dict[str, Any]:
        analysis = self.evaluate(ligne)
        risk = analysis["risk_analysis"]
        lead_time = analysis["lead_time_analysis"]
        cashflow = analysis["cashflow_analysis"]
        moq = analysis["moq_analysis"]
        complexity = analysis["complexity_analysis"]

        return {
            **ligne,
            "PROCUREMENT_ANALYSIS": analysis,
            "GLOBAL_RISK_SCORE": risk["global_risk_score"],
            "RISK_LEVEL": risk["risk_level"],
            "SUPPLIER_RISK_SCORE": risk["supplier_risk"],
            "COUNTRY_RISK_SCORE": risk["country_risk"],
            "LOGISTICS_RISK_SCORE": risk["logistics_risk"],
            "PROJECT_RISK_SCORE": risk["project_risk"],
            "TOTAL_IMPORT_LEAD_TIME": lead_time["total_import_lead_time"],
            "CASHFLOW_SCORE": cashflow["cashflow_score"],
            "CASHFLOW_RISK": cashflow["cashflow_risk"],
            "MOQ_RISK_SCORE": moq["moq_risk_score"],
            "IMPORT_COMPLEXITY_SCORE": complexity["complexity_score"],
            "IMPORT_COMPLEXITY_LEVEL": complexity["complexity_level"],
            # Compatibilite avec DecisionEngine : il lit ces cles simples.
            "lead_time_days": lead_time["total_import_lead_time"],
            "supplier_risk_score": risk["supplier_risk"],
            "logistics_risk_score": risk["logistics_risk"],
        }

    def _final_procurement_score(
        self,
        risk: dict[str, Any],
        lead_time: dict[str, Any],
        cashflow: dict[str, Any],
        moq: dict[str, Any],
        complexity: dict[str, Any],
    ) -> float:
        positive_risk = 100 - float(risk["global_risk_score"])
        positive_lead_time = max(0, 100 - min(float(lead_time["total_import_lead_time"]), 100))
        positive_moq = 100 - float(moq["moq_risk_score"])
        positive_complexity = 100 - float(complexity["complexity_score"])
        score = (
            positive_risk * 0.30
            + positive_lead_time * 0.20
            + float(cashflow["cashflow_score"]) * 0.20
            + positive_moq * 0.15
            + positive_complexity * 0.15
        )
        return round(score, 2)

    def _recommendation(
        self,
        risk: dict[str, Any],
        lead_time: dict[str, Any],
        cashflow: dict[str, Any],
        moq: dict[str, Any],
        complexity: dict[str, Any],
    ) -> dict[str, str]:
        blockers = []
        if risk["risk_level"] in {"HIGH", "CRITICAL"}:
            blockers.append("risque import eleve")
        if lead_time["lead_time_level"] in {"HIGH", "CRITICAL"}:
            blockers.append("delai long")
        if cashflow["cashflow_risk"] in {"HIGH", "CRITICAL"}:
            blockers.append("cashflow tendu")
        if not moq["moq_respected"]:
            blockers.append("MOQ fournisseur non adapte")
        if complexity["complexity_level"] in {"HIGH", "CRITICAL"}:
            blockers.append("complexite import elevee")

        if not blockers:
            return {"decision": "IMPORT", "message": "IMPORT recommande avec risque operationnel maitrise."}
        if len(blockers) <= 2:
            return {"decision": "MIXTE", "message": f"IMPORT possible avec surveillance : {', '.join(blockers)}."}
        return {"decision": "LOCAL", "message": f"LOCAL recommande ou import a securiser : {', '.join(blockers)}."}
