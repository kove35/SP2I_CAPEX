from __future__ import annotations

from typing import Any

from app.ai.excel_mapping_rules import CHAMPS_DQE_MINIMUM
from app.core.ai.ai_anomaly_detector import AIAnomalyDetector
from app.core.ai.ai_column_mapper import AIColumnMapper
from app.core.ai.ai_confidence_engine import AIConfidenceEngine
from app.core.ai.ai_dqe_parser import AIDQEParser
from app.core.ai.ai_excel_classifier import AIExcelClassifier
from app.core.ai.ai_family_mapper import AIFamilyMapper
from app.core.ai.ai_preview_generator import AIPreviewGenerator


class AIExcelOrchestrator:
    """
    Orchestrateur hybride Excel.

    Ordre volontaire :
    1. Heuristiques et regles deterministes.
    2. Fuzzy matching si libelles ambigus.
    3. Point d'extension IA future si la confiance reste faible.
    """

    def __init__(self) -> None:
        self.classifier = AIExcelClassifier()
        self.column_mapper = AIColumnMapper()
        self.dqe_parser = AIDQEParser()
        self.family_mapper = AIFamilyMapper()
        self.anomaly_detector = AIAnomalyDetector()
        self.confidence_engine = AIConfidenceEngine()
        self.preview_generator = AIPreviewGenerator()

    def analyze_sheet(self, sheet_name: str, rows: list[list[Any]]) -> dict[str, Any]:
        candidates = []
        for index, row in enumerate(rows[:30], start=1):
            if sum(1 for value in row if value not in (None, "")) < 3:
                continue
            mapping = self.column_mapper.map_columns(row)
            detected_fields = {item["champ_standard"] for item in mapping}
            score = self._score_sheet(detected_fields, mapping)
            candidates.append((score, index, mapping))

        classification = self.classifier.classify_sheet(sheet_name, rows)
        if not candidates:
            return {
                "feuille": sheet_name,
                "ligne_entete": None,
                "score_dqe": 0,
                "mapping": [],
                "lignes_detectees": 0,
                "classification": classification,
                "avertissements": ["Aucune ligne d'en-tete exploitable detectee."],
                "ai_strategy": "fallback_no_header",
            }

        score, header_line, mapping = max(candidates, key=lambda item: item[0])
        warnings = self._warnings(mapping)

        return {
            "feuille": sheet_name,
            "ligne_entete": header_line,
            "score_dqe": round(score, 2),
            "mapping": mapping,
            "lignes_detectees": self._count_data_rows(rows, header_line),
            "classification": classification,
            "avertissements": warnings,
            "ai_strategy": "rules_then_fuzzy",
        }

    def parse_and_enrich(self, rows: list[list[Any]], analysis: dict[str, Any]) -> dict[str, Any]:
        normalized_rows, classified_rows = self.dqe_parser.parse_rows(rows, analysis)
        enriched_rows = self.family_mapper.enrich_rows(normalized_rows)
        anomalies = self.anomaly_detector.detect(enriched_rows)
        confidence = self.confidence_engine.score(analysis, enriched_rows, anomalies, classified_rows)
        intelligent_preview = self.preview_generator.generate(enriched_rows, analysis, anomalies, confidence)

        return {
            "lignes_normalisees": enriched_rows,
            "classified_rows": classified_rows,
            "anomalies": anomalies,
            "confidence": confidence,
            "intelligent_preview": intelligent_preview,
        }

    def _score_sheet(self, detected_fields: set[str], mapping: list[dict[str, Any]]) -> float:
        minimum_score = len(detected_fields & CHAMPS_DQE_MINIMUM) / len(CHAMPS_DQE_MINIMUM)
        comfort_score = len(detected_fields & {"lot", "batiment", "niveau", "unite", "prix_unitaire_ht"}) / 5
        confidence_score = sum(item["confiance"] for item in mapping) / len(mapping) if mapping else 0
        return min((minimum_score * 0.58) + (comfort_score * 0.22) + (confidence_score * 0.20), 1)

    def _warnings(self, mapping: list[dict[str, Any]]) -> list[str]:
        detected_fields = {item["champ_standard"] for item in mapping}
        missing = sorted(CHAMPS_DQE_MINIMUM - detected_fields)
        warnings = []
        if missing:
            warnings.append(f"Champs minimum non detectes: {', '.join(missing)}.")
        ambiguous = [item["colonne_excel"] for item in mapping if item.get("confiance", 0) < 0.75]
        if ambiguous:
            warnings.append(f"Colonnes a valider humainement: {', '.join(ambiguous)}.")
        return warnings

    def _count_data_rows(self, rows: list[list[Any]], header_line: int) -> int:
        return sum(1 for row in rows[header_line:] if sum(1 for value in row if value not in (None, "")) >= 3)
