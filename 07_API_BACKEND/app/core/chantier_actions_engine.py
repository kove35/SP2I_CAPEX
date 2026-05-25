from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.risk_engine import RiskEngine
from app.core.site_logistics_engine import SiteLogisticsEngine


@dataclass
class ActionRecommendation:
    """Recommandation d'action structurée pour le chantier."""

    action_type: str
    title: str
    problem: str
    impact: str
    recommended_action: str
    priority: str
    risk_level: str
    responsible_role: str
    delivery_eta_days: float = 0
    delay_days: float = 0
    storage_impact: float = 0
    criticality_score: float = 0


class ChantierActionsEngine:
    """
    Transforme les problèmes détectés en actions opérationnelles structurées.

    Le moteur écoute les signaux de:
    - RiskEngine: risques fournisseur, pays, logistique, chantier
    - SiteLogisticsEngine: stockage, saturation, livraison
    - Procurement: arbitrages bloquants ou à valider
    - Simulation: lots critiques, ETA, impacts

    Chaque problème génère une action avec:
    - titre explicite
    - responsable
    - deadline
    - impact chantier
    - dépendances
    """

    def __init__(self) -> None:
        self.risk_engine = RiskEngine()
        self.site_logistics_engine = SiteLogisticsEngine()

    def recommend_actions_from_procurement(
        self,
        decision: dict[str, Any],
        simulation_line: dict[str, Any] | None = None,
    ) -> list[ActionRecommendation]:
        """
        Génère les actions opérationnelles depuis une décision achat.

        Un arbitrage achat doit déclencher zéro, une ou plusieurs actions chantier
        selon son statut, ses risques et ses impacts logistiques.
        """
        actions: list[ActionRecommendation] = []

        if not decision:
            return actions

        validation_status = str(decision.get("validation_status") or "").upper()
        ai_decision = str(decision.get("ai_decision") or "").upper()
        risk_level = str(decision.get("risk_level") or "MEDIUM").upper()
        purchase_mode = str(decision.get("purchase_mode") or "").upper()

        # Problème 1: Arbitrage bloquant à valider
        if validation_status in {"REVIEW_REQUIRED", "TO_ARBITRATE", "BLOCKED"}:
            actions.append(
                ActionRecommendation(
                    action_type="PROCUREMENT",
                    title="Finaliser l'arbitrage achat",
                    problem=f"Arbitrage {ai_decision} à valider par l'équipe achat.",
                    impact="Impact planning: arbitrage bloqué retarde la commande et risque l'ETA chantier.",
                    recommended_action="Valider l'arbitrage et confirmer le fournisseur sélectionné.",
                    priority="CRITICAL" if validation_status == "BLOCKED" else "HIGH",
                    risk_level="CRITICAL" if validation_status == "BLOCKED" else "HIGH",
                    responsible_role="Responsable achat",
                    criticality_score=85 if validation_status == "BLOCKED" else 70,
                )
            )

        # Problème 2: Import à délai critique
        if purchase_mode == "IMPORT" and risk_level in {"HIGH", "CRITICAL"}:
            lead_time = self._number(decision.get("estimated_import_cost"), 0)
            actions.append(
                ActionRecommendation(
                    action_type="DELIVERY",
                    title="Sécuriser la livraison import",
                    problem=f"Import à risque {risk_level}: délai fournisseur et logistique incertains.",
                    impact="Impact chantier: retard de livraison bloque le planning.",
                    recommended_action="Confirmer le fournisseur, relancer si délai dépassé, prévoir alternative locale.",
                    priority="CRITICAL" if risk_level == "CRITICAL" else "HIGH",
                    risk_level=risk_level,
                    responsible_role="Responsable chantier + achat",
                    delivery_eta_days=self._number(simulation_line.get("lead_time_total"), 80) if simulation_line else 80,
                )
            )

        # Problème 3: Stockage insuffisant
        if simulation_line and self._number(simulation_line.get("storage_cost"), 0) > 0:
            storage_impact = self._number(simulation_line.get("storage_cost"), 0)
            actions.append(
                ActionRecommendation(
                    action_type="STORAGE",
                    title="Consolider la capacité de stockage chantier",
                    problem=f"Livraison nécessite {storage_impact:.0f} FCFA de stockage supplémentaire.",
                    impact="Impact site: saturation du stockage risque de retarder la séquence de pose.",
                    recommended_action="Réserver la zone de stockage, valider la fenêtre d'arrivée, coordonner avec le planning chantier.",
                    priority="HIGH",
                    risk_level="MEDIUM",
                    responsible_role="Conducteur travaux",
                    storage_impact=storage_impact,
                )
            )

        # Problème 4: Lot critique
        if simulation_line and self._number(simulation_line.get("criticality_score"), 0) >= 70:
            criticality = self._number(simulation_line.get("criticality_score"), 0)
            actions.append(
                ActionRecommendation(
                    action_type="RISK",
                    title="Arbitrer et sécuriser le lot critique",
                    problem=f"Lot critique (score {criticality:.0f}/100) est un chemin critique du chantier.",
                    impact="Impact planning: tout retard sur ce lot impacte l'ensemble du planning chantier.",
                    recommended_action="Prioriser cet arbitrage, confirmer le fournisseur, mettre en place un suivi bi-hebdomadaire.",
                    priority="CRITICAL",
                    risk_level="CRITICAL",
                    responsible_role="Responsable chantier",
                    criticality_score=criticality,
                )
            )

        return actions

    def recommend_actions_from_risks(
        self,
        risk_evaluation: dict[str, Any],
        simulation_line: dict[str, Any],
    ) -> list[ActionRecommendation]:
        """
        Génère les actions depuis une évaluation de risque.

        Les risques élevés ou critiques doivent déclencher des actions de mitigation.
        """
        actions: list[ActionRecommendation] = []

        if not risk_evaluation or not simulation_line:
            return actions

        global_risk = self._number(risk_evaluation.get("global_risk_score"), 0)
        supplier_risk = self._number(risk_evaluation.get("supplier_risk"), 0)
        country_risk = self._number(risk_evaluation.get("country_risk"), 0)
        logistics_risk = self._number(risk_evaluation.get("logistics_risk"), 0)

        # Action 1: Risque fournisseur
        if supplier_risk >= 70:
            actions.append(
                ActionRecommendation(
                    action_type="PROCUREMENT",
                    title="Renforcer le suivi fournisseur",
                    problem=f"Risque fournisseur élevé ({supplier_risk:.0f}/100): fiabilité ou qualité questionnable.",
                    impact="Impact livraison: risque de retard ou de non-conformité à réception.",
                    recommended_action="Mettre en place un suivi renforcé, demander des attestations qualité, prévoir une alternative.",
                    priority="HIGH",
                    risk_level="HIGH",
                    responsible_role="Responsable achat",
                )
            )

        # Action 2: Risque pays/logistique
        if country_risk >= 70 or logistics_risk >= 70:
            actions.append(
                ActionRecommendation(
                    action_type="LOGISTICS",
                    title="Renforcer le suivi logistique",
                    problem=f"Risque logistique/douane élevé: délai ou surcoût risqué.",
                    impact="Impact planning: risque de retard import => impact chantier.",
                    recommended_action="Confirmer les dates de départ/arrivée, relancer le transitaire, prévoir marges de délai.",
                    priority="HIGH",
                    risk_level="HIGH",
                    responsible_role="Responsable chantier",
                    delivery_eta_days=self._number(simulation_line.get("lead_time_total"), 80),
                )
            )

        # Action 3: Risque global critique
        if global_risk >= 80:
            actions.append(
                ActionRecommendation(
                    action_type="RISK",
                    title="Activer la cellule de crise arbitrage",
                    problem=f"Risque global CRITIQUE ({global_risk:.0f}/100): combinaison de plusieurs facteurs de risque.",
                    impact="Impact maximum: risque de non-livraison ou retard majeur sur chemin critique.",
                    recommended_action="Réunir achat + chantier + direction, définir plan de mitigation, activer alternatives.",
                    priority="CRITICAL",
                    risk_level="CRITICAL",
                    responsible_role="Responsable chantier",
                    criticality_score=global_risk,
                )
            )

        return actions

    def recommend_actions_from_logistics(
        self,
        logistics_evaluation: dict[str, Any],
        simulation_line: dict[str, Any],
    ) -> list[ActionRecommendation]:
        """
        Génère les actions depuis une évaluation de logistique chantier.
        """
        actions: list[ActionRecommendation] = []

        if not logistics_evaluation or not simulation_line:
            return actions

        delivery_risk = str(logistics_evaluation.get("delivery_risk") or "").upper()
        saturation = self._number(logistics_evaluation.get("site_saturation_rate"), 0)
        storage_cost = self._number(logistics_evaluation.get("storage_cost"), 0)

        # Action 1: Saturation du site
        if saturation > 0.8:
            actions.append(
                ActionRecommendation(
                    action_type="STORAGE",
                    title="Gérer l'arrivée chantier (site saturé)",
                    problem=f"Saturation du site: {saturation * 100:.0f}% de la capacité.",
                    impact="Impact séquençage: livraison trop tôt encombre le site, trop tard bloque le planning.",
                    recommended_action="Affiner la fenêtre d'arrivée, coordonner avec les équipes de pose, prévoir zone tampon.",
                    priority="HIGH",
                    risk_level="MEDIUM",
                    responsible_role="Conducteur travaux",
                    storage_impact=storage_cost,
                )
            )

        # Action 2: ETA à risque
        if delivery_risk in {"HIGH", "CRITICAL"}:
            actions.append(
                ActionRecommendation(
                    action_type="DELIVERY",
                    title="Sécuriser l'arrivée chantier",
                    problem=f"Livraison à risque: ETA ou disponibilité stockage incertaine.",
                    impact="Impact planning: retard ou absence bloque les étapes suivantes.",
                    recommended_action="Relancer fournisseur, confirmer transport local, coordonner réception.",
                    priority="CRITICAL" if delivery_risk == "CRITICAL" else "HIGH",
                    risk_level=delivery_risk,
                    responsible_role="Conducteur travaux",
                    delivery_eta_days=self._number(simulation_line.get("lead_time_total"), 80),
                )
            )

        return actions

    def _number(self, value: any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
