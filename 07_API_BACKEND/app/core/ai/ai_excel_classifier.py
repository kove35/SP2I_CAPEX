from __future__ import annotations

from typing import Any

from app.ai.excel_mapping_rules import normaliser_libelle


class AIExcelClassifier:
    """Classifie une feuille Excel selon son vocabulaire et sa structure."""

    DOCUMENT_KEYWORDS = {
        "DQE": {"designation", "quantite", "qte", "prix", "montant", "lot", "unite"},
        "BPU": {"prix", "unitaire", "bordereau", "bpu", "designation"},
        "METRE": {"metre", "surface", "volume", "longueur", "largeur", "hauteur", "quantite"},
        "PLANNING": {"planning", "date", "debut", "fin", "jalon", "delai"},
        "LOGISTIQUE": {"container", "shipment", "eta", "port", "douane", "freight"},
        "FOURNISSEUR": {"fournisseur", "supplier", "contact", "pays", "delai"},
        "CASHFLOW": {"cashflow", "paiement", "acompte", "avance", "tresorerie"},
        "PROCUREMENT": {"achat", "procurement", "commande", "moq", "incoterm"},
        "RECAP": {"recap", "total", "synthese", "resume"},
    }

    def classify_sheet(self, sheet_name: str, rows: list[list[Any]]) -> dict[str, Any]:
        tokens = self._extract_tokens(sheet_name, rows)
        scores: dict[str, float] = {}

        for document_type, keywords in self.DOCUMENT_KEYWORDS.items():
            hits = len(tokens & {normaliser_libelle(keyword) for keyword in keywords})
            density_bonus = self._density_bonus(document_type, rows)
            scores[document_type] = min((hits / max(len(keywords), 1)) + density_bonus, 1.0)

        best_type = max(scores, key=scores.get) if scores else "INCONNU"
        confidence = round(scores.get(best_type, 0), 2)
        if confidence < 0.18:
            best_type = "INCONNU"

        return {
            "document_type": best_type,
            "confidence": confidence,
            "scores": {key: round(value, 2) for key, value in scores.items()},
            "reason": f"Classification basee sur le vocabulaire detecte dans '{sheet_name}'.",
        }

    def _extract_tokens(self, sheet_name: str, rows: list[list[Any]]) -> set[str]:
        values = [sheet_name]
        for row in rows[:40]:
            values.extend(str(value) for value in row if value not in (None, ""))
        return {token for value in values for token in normaliser_libelle(value).split("_") if token}

    def _density_bonus(self, document_type: str, rows: list[list[Any]]) -> float:
        if not rows:
            return 0.0
        non_empty_rows = [row for row in rows if sum(1 for value in row if value not in (None, "")) >= 3]
        density = len(non_empty_rows) / max(len(rows), 1)
        if document_type in {"DQE", "BPU", "METRE"} and density >= 0.35:
            return 0.08
        return 0.0
