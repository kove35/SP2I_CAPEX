from __future__ import annotations

from typing import Any


class ExplainabilityEngine:
    """Generateur de commentaires interpretables pour chaque ligne de simulation."""

    @staticmethod
    def explain_line(line: dict[str, Any]) -> dict[str, Any]:
        decision = line.get("DECISION_FINALE", line.get("DECISION_IMPORT", "LOCAL"))
        score = float(line.get("FINAL_DECISION_SCORE", 0.0) or 0.0)
        importability = float(line.get("IMPORTABILITY_SCORE", 0.0) or 0.0)
        procurement_score = float(line.get("PROCUREMENT_SCORE", 0.0) or 0.0)
        hidden_savings = float(line.get("HIDDEN_SAVINGS_POTENTIAL", 0.0) or 0.0)
        risk_level = line.get("RISK_LEVEL", "UNKNOWN")

        direction = ExplainabilityEngine._build_direction_message(decision, score, importability)
        procurement = ExplainabilityEngine._build_procurement_message(procurement_score, hidden_savings, line)
        technique = ExplainabilityEngine._build_technical_message(line)
        finance = ExplainabilityEngine._build_financial_message(line, hidden_savings)

        return {
            "decision": decision,
            "confidence_score": score,
            "importance": "HIGH" if hidden_savings > 0 or importability < 50 else "MEDIUM",
            "summary": direction,
            "direction": direction,
            "procurement": procurement,
            "technical": technique,
            "financial": finance,
            "risk_level": risk_level,
        }

    @staticmethod
    def _build_direction_message(decision: str, score: float, importability: float) -> str:
        if decision == "IMPORT":
            return (
                f"La ligne est conseillee pour import car le score global est {score:.1f} et "
                f"l'importabilite est de {importability:.1f}%."
            )
        if decision == "MIXTE":
            return (
                f"Le choix mixte est recommande : le score est {score:.1f} et la ligne peut etre partiellement importee "
                f"avec un importabilite de {importability:.1f}%."
            )
        return (
            f"La priorite locale est confirmee car le score global est {score:.1f}. "
            f"Verifier si les risques et les temps de delai supportent un import."
        )

    @staticmethod
    def _build_procurement_message(procurement_score: float, hidden_savings: float, line: dict[str, Any]) -> dict[str, Any]:
        insights: dict[str, Any] = {
            "procurement_score": procurement_score,
            "hidden_savings_potential": hidden_savings,
            "supplier_maturity_score": line.get("SUPPLIER_MATURITY_SCORE", 0),
            "procurement_maturity_score": line.get("PROCUREMENT_MATURITY_SCORE", 0),
        }
        if hidden_savings > 0:
            insights["message"] = (
                "Une opportunite d'economie presentee par le fournisseur, "
                f"avec un potentiel d'economie de {hidden_savings:.2f}."
            )
        else:
            insights["message"] = (
                "Aucun gain cache detecte; concentrez-vous sur la capacite du fournisseur "
                "et la fiabilite des donnees pour renforcer la decision."
            )
        return insights

    @staticmethod
    def _build_technical_message(line: dict[str, Any]) -> dict[str, Any]:
        strategy = line.get("CONTAINER_STRATEGY") or line.get("container_strategy") or "N/A"
        fill_rate = float(line.get("FILL_RATE", 0.0) or 0.0)
        return {
            "container_strategy": strategy,
            "fill_rate": fill_rate,
            "storage_cost": float(line.get("STORAGE_COST", 0.0) or 0.0),
            "message": (
                "Verifier le taux de remplissage de conteneur et les couts de stockage pour assurer "
                "la faisabilite logistique de l'import."
            ),
        }

    @staticmethod
    def _build_financial_message(line: dict[str, Any], hidden_savings: float) -> dict[str, Any]:
        capex_local = float(line.get("CAPEX_LOCAL", 0.0) or 0.0)
        capex_import = float(line.get("CAPEX_IMPORT", 0.0) or 0.0)
        economy = float(line.get("ECONOMIE_NETTE", 0.0) or 0.0)
        return {
            "capex_local": capex_local,
            "capex_import": capex_import,
            "economie_nette": economy,
            "hidden_savings_potential": hidden_savings,
            "message": (
                "Les benefices se mesurent sur l'ecart entre CAPEX local et CAPEX import. "
                "Les potentiels caches renforcent la priorite d'ici."
            ),
        }
