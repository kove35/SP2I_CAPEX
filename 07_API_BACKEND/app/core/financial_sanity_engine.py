from __future__ import annotations

from typing import Any

from app.core.anomaly_detection_engine import AnomalyDetectionEngine
from app.core.equipment_classification_engine import EquipmentClassificationEngine
from app.core.financial_reference_engine import FinancialReferenceEngine


class FinancialSanityEngine:
    """Valide la coherence financiere d'une ligne CAPEX avec audit explicable."""

    def __init__(
        self,
        classifier: EquipmentClassificationEngine | None = None,
        reference_engine: FinancialReferenceEngine | None = None,
        anomaly_engine: AnomalyDetectionEngine | None = None,
    ) -> None:
        self.classifier = classifier or EquipmentClassificationEngine()
        self.reference_engine = reference_engine or FinancialReferenceEngine()
        self.anomaly_engine = anomaly_engine or AnomalyDetectionEngine()

    def validate_line(self, line: dict[str, Any]) -> dict[str, Any]:
        classification = self.classifier.classify_line(line)
        price = self._number(line.get("prix_total_ht") or line.get("CAPEX_LOCAL"), 0)
        reference = classification.get("financial_reference", {})
        benchmark = self.reference_engine.benchmark_price(
            classification.get("equipment_type"),
            price,
            region=str(line.get("region", "CENTRAL_AFRICA")),
        )
        anomalies = self.anomaly_engine.detect_line_anomalies(line, reference)
        anomaly_score = self.anomaly_engine.score_anomalies(anomalies)
        confidence = max(0.0, min(100.0, benchmark.get("financial_confidence_score", 25.0) - anomaly_score * 0.45))
        return {
            "classification": classification,
            "benchmark": benchmark,
            "anomalies": anomalies,
            "anomaly_score": anomaly_score,
            "financial_confidence_score": round(confidence, 2),
            "semantic_confidence_score": classification.get("semantic_confidence_score", 0),
            "procurement_confidence_score": classification.get("procurement_confidence_score", 0),
            "explainability": self._explain(classification, reference, anomalies),
            "powerbi": self._powerbi_payload(classification, confidence, anomaly_score),
        }

    def _explain(self, classification: dict[str, Any], reference: dict[str, Any], anomalies: list[dict[str, Any]]) -> str:
        if not reference:
            return "Aucun referentiel financier disponible pour cet equipement."
        label = classification.get("equipment_type", "equipement")
        price_min = reference.get("price_min")
        price_max = reference.get("price_max")
        if anomalies:
            return (
                f"Le prix detecte semble incoherent pour {label}. "
                f"Le referentiel Afrique centrale indique une plage realiste entre {price_min:,.0f} "
                f"et {price_max:,.0f} FCFA."
            )
        return (
            f"Le prix detecte est coherent pour {label}. "
            f"Le range de reference est {price_min:,.0f} a {price_max:,.0f} FCFA."
        )

    def _powerbi_payload(self, classification: dict[str, Any], confidence: float, anomaly_score: float) -> dict[str, Any]:
        return {
            "family": classification.get("family"),
            "subcategory": classification.get("subcategory"),
            "equipment_type": classification.get("equipment_type"),
            "financial_confidence_score": round(confidence, 2),
            "anomaly_score": anomaly_score,
            "heatmap_bucket": "HIGH_RISK" if anomaly_score >= 45 else "WATCH" if anomaly_score else "OK",
        }

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
