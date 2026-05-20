from __future__ import annotations

from typing import Any

from app.core.procurement_engine import ProcurementEngine


class ProcurementEnrichmentEngine:
    """Enrichit les lignes CAPEX avec des signaux procurement enterprise.

    Cette couche s'appuie sur le moteur `ProcurementEngine` existant pour
    conserver la logique métier actuelle et ajoute des scores d'importability,
    de sourcing, de maturité fournisseur et des économies cachées.
    """

    def __init__(self, base_engine: ProcurementEngine | None = None) -> None:
        self.base_engine = base_engine or ProcurementEngine()

    def enrich_line(self, ligne: dict[str, Any]) -> dict[str, Any]:
        resultat = self.base_engine.enrich_line(ligne)
        ligne_enrichie = {**ligne, **resultat}
        analyse = self._compute_procurement_signals(ligne_enrichie)
        return {**ligne_enrichie, **analyse}

    def _compute_procurement_signals(self, ligne: dict[str, Any]) -> dict[str, Any]:
        sourcing_coverage = self._score_sourcing_coverage(ligne)
        supplier_maturity = self._score_supplier_maturity(ligne)
        procurement_maturity = self._score_procurement_maturity(ligne, sourcing_coverage, supplier_maturity)
        importability = self._score_importability(ligne, sourcing_coverage, procurement_maturity)
        import_confidence = self._score_import_confidence(ligne)
        hidden_savings = self._hidden_savings_potential(ligne, importability)
        procurement_score = self._score_procurement(
            line=ligne,
            sourcing_coverage=sourcing_coverage,
            supplier_maturity=supplier_maturity,
            procurement_maturity=procurement_maturity,
            importability=importability,
            import_confidence=import_confidence,
        )

        procurement_analysis = {
            **ligne.get("PROCUREMENT_ANALYSIS", {}),
            "sourcing_coverage": sourcing_coverage,
            "supplier_maturity_score": supplier_maturity,
            "procurement_maturity_score": procurement_maturity,
            "importability_score": importability,
            "import_confidence_score": round(import_confidence, 2),
            "hidden_savings_potential": hidden_savings,
            "procurement_score": procurement_score,
        }

        return {
            "SOURCING_COVERAGE": round(sourcing_coverage, 2),
            "IMPORT_CONFIDENCE_SCORE": round(self._score_import_confidence(ligne), 2),
            "SUPPLIER_MATURITY_SCORE": round(supplier_maturity, 2),
            "PROCUREMENT_MATURITY_SCORE": round(procurement_maturity, 2),
            "IMPORTABILITY_SCORE": round(importability, 2),
            "HIDDEN_SAVINGS_POTENTIAL": round(hidden_savings, 2),
            "PROCUREMENT_SCORE": round(procurement_score, 2),
            "PROCUREMENT_ANALYSIS": procurement_analysis,
        }

    def _score_import_confidence(self, ligne: dict[str, Any]) -> float:
        score = 50.0
        if ligne.get("prix_fob") is not None:
            score += 20.0
        supplier_confidence = self._number(ligne.get("source_confidence"), 0)
        score += min(supplier_confidence * 25.0, 20.0)
        if ligne.get("quality_score") is not None:
            score += min(float(ligne.get("quality_score", 0)) / 100 * 20.0, 20.0)
        return min(max(score, 0), 100)

    def _score_sourcing_coverage(self, ligne: dict[str, Any]) -> float:
        score = 0.0
        if ligne.get("prix_fob") is not None:
            score += 30.0
        if ligne.get("supplier_moq") is not None and ligne.get("QTE") is not None:
            moq = self._number(ligne.get("supplier_moq"), 0)
            quantite = self._number(ligne.get("QTE"), 0)
            if moq and quantite >= moq:
                score += 25.0
            elif moq:
                score += 10.0
        if ligne.get("famille"):
            score += 15.0
        score += min(self._number(ligne.get("quality_score"), 50) / 100 * 15.0, 15.0)
        score += min(self._number(ligne.get("reliability_score"), 50) / 100 * 15.0, 15.0)
        return min(max(score, 0), 100)

    def _score_supplier_maturity(self, ligne: dict[str, Any]) -> float:
        quality = self._number(ligne.get("quality_score"), 50)
        reliability = self._number(ligne.get("reliability_score"), 50)
        if quality == 0 and reliability == 0:
            return 40.0
        return (quality * 0.55 + reliability * 0.45) if quality or reliability else 40.0

    def _score_procurement_maturity(self, ligne: dict[str, Any], sourcing_coverage: float, supplier_maturity: float) -> float:
        completeness = 0.0
        if ligne.get("prix_fob") is not None:
            completeness += 20.0
        if ligne.get("supplier_moq") is not None:
            completeness += 20.0
        if ligne.get("volume_unitaire_m3") is not None and ligne.get("poids_unitaire_kg") is not None:
            completeness += 20.0
        if ligne.get("supplier_city") and ligne.get("departure_port") and ligne.get("arrival_port"):
            completeness += 20.0
        if ligne.get("project_criticality"):
            completeness += 20.0
        return min((sourcing_coverage * 0.4 + supplier_maturity * 0.3 + completeness * 0.3), 100)

    def _score_importability(self, ligne: dict[str, Any], sourcing_coverage: float, procurement_maturity: float) -> float:
        risk_penalty = self._number(ligne.get("logistics_risk"), 50)
        lead_time_days = self._number(ligne.get("lead_time_days") or ligne.get("TOTAL_IMPORT_LEAD_TIME"), 45)
        container_bonus = min(max(self._number(ligne.get("FILL_RATE"), 0), 0), 1) * 15.0
        base = sourcing_coverage * 0.5 + procurement_maturity * 0.25 + container_bonus
        penalty = min(risk_penalty / 100 * 20.0 + min(lead_time_days / 90 * 20.0, 20.0), 40.0)
        return min(max(base - penalty, 0), 100)

    def _hidden_savings_potential(self, ligne: dict[str, Any], importability: float) -> float:
        capex_local = self._number(ligne.get("CAPEX_LOCAL") or ligne.get("MONTANT_LOCAL"), 0)
        capex_import = self._number(ligne.get("CAPEX_IMPORT"), 0)
        if capex_local <= capex_import:
            return 0.0
        leverage = importability / 100
        return max(0.0, (capex_local - capex_import) * min(leverage, 1.0))

    def _score_procurement(
        self,
        line: dict[str, Any],
        sourcing_coverage: float,
        supplier_maturity: float,
        procurement_maturity: float,
        importability: float,
        import_confidence: float,
    ) -> float:
        return min(
            (sourcing_coverage * 0.20)
            + (supplier_maturity * 0.20)
            + (procurement_maturity * 0.20)
            + (importability * 0.25)
            + (import_confidence * 0.15),
            100,
        )

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (ValueError, TypeError):
            return default
