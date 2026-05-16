from __future__ import annotations


class AIConfidenceEngine:
    """Produit un score global lisible a partir des sous-scores IA."""

    def score(
        self,
        sheet_analysis: dict,
        rows: list[dict],
        anomalies: list[dict],
        classified_rows: list[dict],
    ) -> dict:
        mapping_score = self._average([item.get("confiance", 0) for item in sheet_analysis.get("mapping", [])])
        structure_score = self._structure_score(classified_rows)
        anomaly_penalty = min(len(anomalies) / max(len(rows), 1), 1)
        data_score = max(1 - anomaly_penalty, 0)
        global_score = (mapping_score * 0.35) + (structure_score * 0.30) + (data_score * 0.25) + (sheet_analysis.get("score_dqe", 0) * 0.10)

        return {
            "global_confidence": round(global_score, 2),
            "mapping_quality": round(mapping_score, 2),
            "structure_quality": round(structure_score, 2),
            "data_quality": round(data_score, 2),
            "needs_human_validation": global_score < 0.82 or bool(anomalies),
            "reason": "Score combine mapping, structure DQE, anomalies et score feuille.",
        }

    def _average(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else 0

    def _structure_score(self, classified_rows: list[dict]) -> float:
        if not classified_rows:
            return 0
        article_rows = sum(1 for row in classified_rows if row.get("row_type") == "article")
        lot_rows = sum(1 for row in classified_rows if row.get("row_type") == "lot")
        return min((article_rows / len(classified_rows)) + (0.08 if lot_rows else 0), 1)
