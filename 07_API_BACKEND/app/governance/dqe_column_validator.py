from __future__ import annotations

from typing import Any

from app.ai.excel_mapping_rules import normaliser_libelle
from app.governance.dqe_issue_builder import build_dqe_issue


FIELD_ALIASES = {
    "designation": ["DESIGNATION", "LIBELLE", "DESCRIPTION", "ARTICLE", "OUVRAGE"],
    "quantity": ["QTE", "QUANTITE", "QUANTITY", "QTY"],
    "unit": ["UNITE", "U", "UNIT"],
    "local_unit_price": ["PU_LOCAL", "PU_ESTIME_LOCAL_FCFA", "PRIX_UNITAIRE", "PU", "P.U"],
    "local_total_amount": ["MONTANT_LOCAL", "TOTAL_LOCAL", "TOTAL_HT", "MONTANT_HT", "PRIX_TOTAL", "CAPEX_LOCAL_MONTANT"],
    "lot": ["LOT", "CORPS_ETAT", "POSTE"],
    "family": ["FAMILLE", "FAMILY", "FAMILLE_METIER"],
    "code_bpu": ["CODE_BPU", "BPU_CODE", "CODE_ARTICLE"],
    "niveau": ["NIVEAU", "ETAGE", "LEVEL"],
    "batiment": ["BATIMENT", "BAT", "BUILDING", "BLOC"],
}

FIELD_LABELS = {
    "designation": "Designation",
    "quantity": "Quantite",
    "unit": "Unite",
    "local_unit_price": "Prix unitaire local",
    "local_total_amount": "Montant local",
    "lot": "Lot",
    "family": "Famille",
    "code_bpu": "Code BPU",
    "niveau": "Niveau",
    "batiment": "Batiment",
}

STANDARD_TO_PUBLIC_FIELD = {
    "designation": "designation",
    "quantite": "quantity",
    "unite": "unit",
    "prix_unitaire_ht": "local_unit_price",
    "prix_total_ht": "local_total_amount",
    "lot": "lot",
    "famille": "family",
    "niveau": "niveau",
    "batiment": "batiment",
    "id_ligne": "code_bpu",
}

REQUIRED_GROUPS = (
    ("designation", {"designation"}),
    ("quantity", {"quantity"}),
    ("price_or_amount", {"local_unit_price", "local_total_amount"}),
)

RECOMMENDED_FIELDS = ("unit", "lot", "family", "code_bpu", "niveau", "batiment")


def validate_dqe_columns(
    columns: list[Any],
    mapping: list[dict[str, Any]],
    sheet_name: str,
) -> list[dict[str, Any]]:
    available_columns = [str(column) for column in columns if column not in (None, "")]
    normalized_columns = {normaliser_libelle(column): str(column) for column in available_columns}
    mapped_fields = {
        STANDARD_TO_PUBLIC_FIELD.get(str(item.get("champ_standard") or ""), str(item.get("champ_standard") or ""))
        for item in mapping
    }
    issues: list[dict[str, Any]] = []

    if not available_columns:
        issues.append(build_dqe_issue("HEADER_NOT_FOUND", sheet_name=sheet_name))
        return issues

    for field, alternatives in REQUIRED_GROUPS:
        if not (mapped_fields & alternatives):
            label = "Prix ou montant" if field == "price_or_amount" else FIELD_LABELS.get(field, field)
            expected_aliases = sorted({alias for alt in alternatives for alias in FIELD_ALIASES.get(alt, [])})
            issues.append(
                build_dqe_issue(
                    "MISSING_REQUIRED_COLUMN",
                    field=field,
                    label=label,
                    sheet_name=sheet_name,
                    expected_value=f"Une colonne {label.lower()} reconnue",
                    expected_aliases=expected_aliases,
                    available_columns=available_columns,
                )
            )

    for field in RECOMMENDED_FIELDS:
        if field not in mapped_fields and not _has_any_alias(normalized_columns, FIELD_ALIASES.get(field, [])):
            issues.append(
                build_dqe_issue(
                    "RECOMMENDED_COLUMN_MISSING",
                    field=field,
                    label=FIELD_LABELS.get(field, field),
                    sheet_name=sheet_name,
                    expected_aliases=FIELD_ALIASES.get(field, []),
                    available_columns=available_columns,
                )
            )

    ambiguous_price_labels = {"pu", "prix_unitaire", "prix"}
    for normalized, original in normalized_columns.items():
        if normalized in ambiguous_price_labels:
            issues.append(
                build_dqe_issue(
                    "AMBIGUOUS_COLUMN_ALIAS",
                    field="local_unit_price",
                    label="Prix unitaire",
                    sheet_name=sheet_name,
                    column_name=original,
                    detected_value=original,
                    expected_aliases=["PU_LOCAL", "PU_IMPORT", "PU_ESTIME_LOCAL_FCFA"],
                    available_columns=available_columns,
                )
            )

    for item in mapping:
        column = str(item.get("colonne_excel") or "")
        normalized = normaliser_libelle(column)
        if normalized in {"code_bpu", "bpu_code", "code_prix"} and item.get("champ_standard") in {"prix_unitaire_ht", "prix_total_ht"}:
            issues.append(
                build_dqe_issue(
                    "FORBIDDEN_PRICE_MAPPING",
                    field="code_bpu",
                    label="Code BPU",
                    sheet_name=sheet_name,
                    column_name=column,
                    detected_value=column,
                    expected_value="Identifiant article, pas un prix",
                    available_columns=available_columns,
                )
            )

    return issues


def _has_any_alias(normalized_columns: dict[str, str], aliases: list[str]) -> bool:
    normalized_aliases = {normaliser_libelle(alias) for alias in aliases}
    return any(alias in normalized_columns for alias in normalized_aliases)
