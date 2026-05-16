from __future__ import annotations

from typing import Any

from app.core import clean_lot, clean_niveau, nettoyer_nombre


class AIDQEParser:
    """
    Parser DQE explicable.

    Il memorise le lot courant et classe chaque ligne avant normalisation. Les
    lignes structurelles restent tracees mais ne deviennent pas des articles.
    """

    def parse_rows(
        self,
        rows: list[list[Any]],
        analysis: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        header_line = analysis.get("ligne_entete")
        if not header_line:
            return [], []

        columns = {item["champ_standard"]: item["colonne_index"] for item in analysis.get("mapping", [])}
        normalized_rows: list[dict[str, Any]] = []
        classified_rows: list[dict[str, Any]] = []
        current_lot = clean_lot(analysis.get("feuille", ""))

        for absolute_index, row in enumerate(rows[header_line:], start=header_line + 1):
            row_type, reason, detected_lot = self.classify_row(row, columns, current_lot)
            if detected_lot:
                current_lot = detected_lot

            classified_rows.append(
                {
                    "row_index": absolute_index,
                    "row_type": row_type,
                    "reason": reason,
                    "current_lot": current_lot,
                }
            )

            if row_type != "article":
                continue

            normalized = self._normalize_article(row, columns, current_lot)
            if normalized:
                normalized_rows.append(normalized)

        return normalized_rows, classified_rows

    def classify_row(
        self,
        row: list[Any],
        columns: dict[str, int],
        current_lot: str,
    ) -> tuple[str, str, str]:
        text = " ".join(str(value) for value in row if value not in (None, "")).strip()
        if not text:
            return "vide", "Ligne vide.", ""

        lot = self._detect_lot(row, columns, text)
        if lot:
            return "lot", f"Contexte lot detecte: {lot}.", lot

        lowered = text.lower()
        if "sous-total" in lowered or lowered.startswith("total") or " total " in lowered:
            return "total", "Ligne de total/sous-total ignoree pour eviter les doubles comptes.", ""

        designation = str(self._value(row, columns, "designation", "")).strip()
        quantity = nettoyer_nombre(self._value(row, columns, "quantite", 0), 0) or 0
        amount = nettoyer_nombre(self._value(row, columns, "prix_total_ht", 0), 0) or 0

        unit_price = nettoyer_nombre(self._value(row, columns, "prix_unitaire_ht", 0), 0) or 0

        if designation and (quantity > 0 or amount > 0 or unit_price > 0) and current_lot:
            return "article", "Designation avec quantite ou montant et contexte lot.", ""

        if designation and not current_lot:
            return "inconnu", "Article potentiel sans lot courant.", ""

        return "commentaire", "Ligne informative ou structure non exploitee.", ""

    def _normalize_article(self, row: list[Any], columns: dict[str, int], current_lot: str) -> dict[str, Any] | None:
        designation = str(self._value(row, columns, "designation", "")).strip()
        if not designation:
            return None

        lot = clean_lot(self._value(row, columns, "lot", "")) or current_lot
        if not lot:
            return None

        quantity = self._value(row, columns, "quantite", 0)
        unit_price = self._value(row, columns, "prix_unitaire_ht", 0)
        total_price = self._value(row, columns, "prix_total_ht", 0)
        numeric_quantity = nettoyer_nombre(quantity, 0) or 0
        numeric_unit_price = nettoyer_nombre(unit_price, 0) or 0
        numeric_total_price = nettoyer_nombre(total_price, 0) or 0
        if numeric_total_price <= 0 and numeric_quantity > 0 and numeric_unit_price > 0:
            total_price = numeric_quantity * numeric_unit_price

        return {
            "id_ligne": str(self._value(row, columns, "id_ligne", "")),
            "lot": lot,
            "batiment": str(self._value(row, columns, "batiment", "")),
            "niveau": clean_niveau(self._value(row, columns, "niveau", "")),
            "designation": designation,
            "unite": str(self._value(row, columns, "unite", "")),
            "quantite": quantity,
            "prix_unitaire_ht": unit_price,
            "prix_total_ht": total_price,
            "source": "ai_hybrid_excel_parser",
        }

    def _detect_lot(self, row: list[Any], columns: dict[str, int], text: str) -> str:
        for value in (self._value(row, columns, "lot", ""), self._value(row, columns, "designation", ""), text):
            lot = clean_lot(value)
            if lot.startswith("LOT "):
                return lot
        return ""

    def _value(self, row: list[Any], columns: dict[str, int], field: str, default: Any = "") -> Any:
        index = columns.get(field)
        if index is None or index >= len(row):
            return default
        value = row[index]
        return default if value is None else value
