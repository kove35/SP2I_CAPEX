from __future__ import annotations

from app.core import nettoyer_nombre


class AIPreviewGenerator:
    """Cree un resume intelligent de l'analyse Excel."""

    def generate(
        self,
        rows: list[dict],
        sheet_analysis: dict,
        anomalies: list[dict],
        confidence: dict,
    ) -> dict:
        lots = {row.get("lot") for row in rows if row.get("lot")}
        recognized_columns = len(sheet_analysis.get("mapping", []))
        ambiguous_columns = sum(1 for item in sheet_analysis.get("mapping", []) if item.get("confiance", 0) < 0.75)
        estimated_capex = sum(nettoyer_nombre(row.get("prix_total_ht"), 0) or 0 for row in rows)

        return {
            "lots_detected": len(lots),
            "recognized_columns": recognized_columns,
            "quality_score": confidence.get("global_confidence", 0),
            "ambiguous_columns": ambiguous_columns,
            "invalid_rows": len(anomalies),
            "estimated_capex_detected": estimated_capex,
            "human_validation_required": confidence.get("needs_human_validation", True),
        }
