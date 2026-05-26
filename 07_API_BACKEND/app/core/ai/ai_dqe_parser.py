from __future__ import annotations

import re
from typing import Any

from app.core import clean_lot, clean_niveau, nettoyer_nombre
from app.governance.rules import assess_parsed_row
from app.utils.id_normalizer import normalize_optional_id


def _texte(valeur: Any) -> str:
    return str(valeur or "").strip()


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
        initial_lot = clean_lot(analysis.get("feuille", ""))
        current_lot = initial_lot if initial_lot.startswith("LOT ") else ""

        for absolute_index, row in enumerate(rows[header_line:], start=header_line + 1):
            row_type, reason, detected_lot = self.classify_row(row, columns, current_lot)
            if detected_lot:
                current_lot = detected_lot

            governance = assess_parsed_row(row_type, reason)
            classified_rows.append(
                {
                    "row_index": absolute_index,
                    "row_type": row_type,
                    "reason": reason,
                    "current_lot": current_lot,
                    "raw_text": self._row_text(row),
                    **governance.as_dict(),
                }
            )

            if row_type != "article":
                continue

            normalized = self._normalize_article(row, columns, current_lot)
            if normalized:
                normalized.update(
                    {
                        "governance_status": governance.governance_status,
                        "trust_score": governance.trust_score,
                        "governance_issues": [issue.as_dict() for issue in governance.governance_issues],
                        "review_required": governance.review_required,
                        "certification_status": governance.certification_status,
                    }
                )
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

        if self._is_analytics_or_ratio_line(text):
            return "ratio_analytics", "Ligne ratio/analytics ignoree pour FACT_METRE.", ""

        lowered = text.lower()
        if "sous-total" in lowered or lowered.startswith("total") or " total " in lowered:
            return "total", "Ligne de total/sous-total ignoree pour eviter les doubles comptes.", ""

        designation = str(self._value(row, columns, "designation", "")).strip()
        if designation and self._is_summary_designation(designation):
            return "total", "Ligne recap/total ignoree pour eviter les doubles comptes.", ""

        quantity = nettoyer_nombre(self._value(row, columns, "quantite", 0), 0) or 0
        amount = nettoyer_nombre(self._value(row, columns, "prix_total_ht", 0), 0) or 0
        import_amount = nettoyer_nombre(self._value(row, columns, "montant_import", 0), 0) or 0
        unit_price = nettoyer_nombre(self._value(row, columns, "prix_unitaire_ht", 0), 0) or 0
        import_unit_price = nettoyer_nombre(self._value(row, columns, "pu_import", 0), 0) or 0
        lot_cell = clean_lot(self._value(row, columns, "lot", ""))
        lot_code = normalize_optional_id(self._value(row, columns, "lot_code", ""))

        has_price_signal = amount > 0 or unit_price > 0 or import_amount > 0 or import_unit_price > 0
        if designation and quantity > 0 and has_price_signal and (current_lot or lot_cell or lot_code):
            return "article", "Designation avec quantite ou montant et contexte lot.", ""

        lot = self._detect_lot(row, columns, text)
        if lot:
            return "lot", f"Contexte lot detecte: {lot}.", lot

        if designation and not current_lot:
            return "inconnu", "Article potentiel sans lot courant.", ""

        return "commentaire", "Ligne informative ou structure non exploitee.", ""

    def _normalize_article(self, row: list[Any], columns: dict[str, int], current_lot: str) -> dict[str, Any] | None:
        designation = str(self._value(row, columns, "designation", "")).strip()
        if not designation:
            return None

        lot = clean_lot(self._value(row, columns, "lot", "")) or normalize_optional_id(self._value(row, columns, "lot_code", "")) or current_lot
        if not lot or self._is_invalid_lot(lot):
            return None

        quantity = self._value(row, columns, "quantite", 0)
        unit_price = self._value(row, columns, "prix_unitaire_ht", 0)
        total_price = self._value(row, columns, "prix_total_ht", 0)
        import_unit_price = self._value(row, columns, "pu_import", 0)
        import_total_price = self._value(row, columns, "montant_import", 0)
        numeric_quantity = nettoyer_nombre(quantity, 0) or 0
        numeric_unit_price = nettoyer_nombre(unit_price, 0) or 0
        numeric_total_price = nettoyer_nombre(total_price, 0) or 0
        numeric_import_unit_price = nettoyer_nombre(import_unit_price, 0) or 0
        numeric_import_total_price = nettoyer_nombre(import_total_price, 0) or 0
        if numeric_total_price <= 0 and numeric_quantity > 0 and numeric_unit_price > 0:
            total_price = numeric_quantity * numeric_unit_price
            numeric_total_price = nettoyer_nombre(total_price, 0) or 0
        if numeric_import_total_price <= 0 and numeric_quantity > 0 and numeric_import_unit_price > 0:
            import_total_price = numeric_quantity * numeric_import_unit_price
            numeric_import_total_price = nettoyer_nombre(import_total_price, 0) or 0

        if numeric_quantity <= 0 or (numeric_total_price <= 0 and numeric_import_total_price <= 0):
            return None

        article_id = normalize_optional_id(self._value(row, columns, "article_id", ""), self._value(row, columns, "id_ligne", ""))
        ifc_guid = normalize_optional_id(self._value(row, columns, "ifc_guid", ""))

        return {
            "id_ligne": article_id or ifc_guid or str(self._value(row, columns, "id_ligne", "")),
            "project_code": normalize_optional_id(self._value(row, columns, "project_code", "")),
            "batiment_code": normalize_optional_id(self._value(row, columns, "batiment_code", "")),
            "niveau_code": normalize_optional_id(self._value(row, columns, "niveau_code", "")),
            "appartement_code": normalize_optional_id(self._value(row, columns, "appartement_code", "")),
            "piece_code": normalize_optional_id(self._value(row, columns, "piece_code", "")),
            "lot_code": normalize_optional_id(self._value(row, columns, "lot_code", "")),
            "sous_lot_code": normalize_optional_id(self._value(row, columns, "sous_lot_code", "")),
            "article_id": article_id,
            "lot": lot,
            "sous_lot": str(self._value(row, columns, "sous_lot", "")) or normalize_optional_id(self._value(row, columns, "sous_lot_code", "")),
            "batiment": str(self._value(row, columns, "batiment", "")) or normalize_optional_id(self._value(row, columns, "batiment_code", "")),
            "niveau": clean_niveau(self._value(row, columns, "niveau", "") or self._value(row, columns, "niveau_code", "")),
            "appart": str(self._value(row, columns, "appart", "")) or normalize_optional_id(self._value(row, columns, "appartement_code", "")),
            "piece": str(self._value(row, columns, "piece", "")) or normalize_optional_id(self._value(row, columns, "piece_code", "")),
            "type_zone": str(self._value(row, columns, "type_zone", "")),
            "code_article": normalize_optional_id(self._value(row, columns, "code_article", ""), self._value(row, columns, "id_ligne", "")),
            "designation": designation,
            "unite": str(self._value(row, columns, "unite", "")),
            "quantite": quantity,
            "formule": str(self._value(row, columns, "formule", "")),
            "bim_object_id": str(self._value(row, columns, "bim_object_id", "")),
            "ifc_guid": ifc_guid,
            "bim_object": str(self._value(row, columns, "bim_object", "")),
            "type_objet": str(self._value(row, columns, "type_objet", "")),
            "famille_bim": str(self._value(row, columns, "famille_bim", "")),
            "systeme": str(self._value(row, columns, "systeme", "")),
            "phase_chantier": str(self._value(row, columns, "phase_chantier", "")),
            "classification": str(self._value(row, columns, "classification", "")),
            "omniclass": str(self._value(row, columns, "omniclass", "")),
            "uniclass": str(self._value(row, columns, "uniclass", "")),
            "ifc_type": str(self._value(row, columns, "ifc_type", "")),
            "prix_unitaire_ht": unit_price,
            "prix_total_ht": total_price,
            "pu_import": import_unit_price,
            "montant_import": import_total_price,
            "decision": str(self._value(row, columns, "decision", "")),
            "fournisseur": str(self._value(row, columns, "fournisseur", "")),
            "execution_status": str(self._value(row, columns, "execution_status", "")),
            "workflow_status": str(self._value(row, columns, "workflow_status", "")),
            "risque": str(self._value(row, columns, "risque", "")),
            "eta": self._value(row, columns, "eta", ""),
            "bim_maturity": str(self._value(row, columns, "bim_maturity", "")),
            "source_file_type": str(self._value(row, columns, "source", "")),
            "source": "ai_hybrid_excel_parser",
        }

    def _detect_lot(self, row: list[Any], columns: dict[str, int], text: str) -> str:
        explicit_lot = clean_lot(self._value(row, columns, "lot", ""))
        if explicit_lot and not self._is_invalid_lot(explicit_lot):
            return explicit_lot

        for value in (self._value(row, columns, "designation", ""), text):
            lot = clean_lot(value)
            if lot.startswith("LOT ") and not self._is_invalid_lot(lot):
                return lot
        return ""

    def _is_invalid_lot(self, lot: Any) -> bool:
        texte = _texte(lot).upper()
        if not texte:
            return True
        if "%" in texte:
            return True
        if nettoyer_nombre(texte, None) is not None:
            return True
        mots_interdits = ("RATIO", "TAUX", "RECAP", "SYNTHESE", "STATISTIQUE", "TOTAL")
        return any(mot in texte for mot in mots_interdits)

    def _is_summary_designation(self, designation: Any) -> bool:
        texte = _texte(designation).lower()
        if not texte:
            return True
        return (
            "%" in texte
            or texte.startswith("total")
            or texte.startswith("sous-total")
            or texte.startswith("sous total")
            or "recap" in texte
            or "rÃ©cap" in texte
            or "synthese" in texte
            or "synthÃ¨se" in texte
        )

    def _is_analytics_or_ratio_line(self, text: str) -> bool:
        valeurs = [_texte(part) for part in text.split() if _texte(part)]
        if "%" in text and len(valeurs) <= 4:
            return True
        lowered = text.lower()
        # Detection par mot entier : "administration" ne doit pas etre rejete
        # sous pretexte qu'il contient la sequence de lettres "ratio".
        return bool(re.search(r"\b(rÃ©partition|repartition|statistique|ratio)\b", lowered))

    def _value(self, row: list[Any], columns: dict[str, int], field: str, default: Any = "") -> Any:
        index = columns.get(field)
        if index is None or index >= len(row):
            return default
        value = row[index]
        return default if value is None else value

    def _row_text(self, row: list[Any]) -> str:
        return " ".join(str(value) for value in row if value not in (None, "")).strip()
