from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from app.ai.excel_mapping_rules import REGLES_MAPPING_EXCEL, normaliser_libelle


class AIColumnMapper:
    """
    Mapping intelligent mais explicable des colonnes Excel.

    Le nom contient "AI" car ce module est le point d'extension futur pour un
    LLM/embeddings. Aujourd'hui il reste deterministe : synonymes metier,
    fuzzy matching et raisons auditable.
    """

    def map_columns(self, header_row: list[Any]) -> list[dict[str, Any]]:
        mapping: list[dict[str, Any]] = []
        mapped_fields: set[str] = set()

        for column_index, label in enumerate(header_row):
            if label in (None, ""):
                continue

            suggestion = self.map_single_column(label)
            if not suggestion or suggestion["mapped_to"] in mapped_fields:
                continue

            mapped_fields.add(suggestion["mapped_to"])
            mapping.append(
                {
                    "colonne_excel": str(label),
                    "colonne_index": column_index,
                    "champ_standard": suggestion["mapped_to"],
                    "confiance": suggestion["confidence"],
                    "raison": suggestion["reason"],
                    "strategy": suggestion["strategy"],
                }
            )

        return mapping

    def map_single_column(self, label: Any) -> dict[str, Any] | None:
        normalized_label = normaliser_libelle(label)
        best_field = ""
        best_keyword = ""
        best_score = 0.0
        best_strategy = "unmapped"

        for rule in REGLES_MAPPING_EXCEL:
            for keyword in rule.mots_cles:
                normalized_keyword = normaliser_libelle(keyword)
                score, strategy = self._score(normalized_label, normalized_keyword)
                if score > best_score:
                    best_field = rule.champ_standard
                    best_keyword = keyword
                    best_score = score
                    best_strategy = strategy

        if best_score < 0.58:
            return None

        return {
            "source_column": str(label),
            "mapped_to": best_field,
            "confidence": round(best_score, 2),
            "reason": f"Colonne rapprochee de '{best_keyword}' par {best_strategy}.",
            "strategy": best_strategy,
        }

    def _score(self, label: str, keyword: str) -> tuple[float, str]:
        if label == keyword:
            return 1.0, "regle exacte"
        compact_label = label.replace("_", "")
        compact_keyword = keyword.replace("_", "")
        if compact_label == compact_keyword:
            return 0.96, "regle exacte compactee"
        if len(keyword) <= 1:
            tokens = set(label.split("_"))
            if keyword in tokens:
                return 0.72, "jeton court exact"
            return 0.0, "mot cle trop court"
        if label.startswith(keyword) or label.endswith(keyword):
            return 0.92, "prefixe/suffixe metier"
        if keyword in label:
            return 0.82, "inclusion metier"

        ratio = SequenceMatcher(None, label, keyword).ratio()
        if ratio >= 0.74:
            return ratio, "fuzzy matching"

        compact_ratio = SequenceMatcher(None, compact_label, compact_keyword).ratio()
        if compact_ratio >= 0.70:
            return compact_ratio, "fuzzy matching compact"

        return 0.0, "aucune correspondance"
