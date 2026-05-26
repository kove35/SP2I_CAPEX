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
    "import_unit_price": ["PU_IMPORT", "PRIX_IMPORT", "PRIX_UNITAIRE_IMPORT"],
    "import_total_amount": ["MONTANT_IMPORT", "CAPEX_IMPORT", "TOTAL_IMPORT"],
    "lot": ["LOT", "CORPS_ETAT", "POSTE"],
    "sous_lot": ["SOUS_LOT", "SOUS LOT", "SUB_LOT"],
    "family": ["FAMILLE", "FAMILY", "FAMILLE_METIER"],
    "code_bpu": ["CODE_BPU", "BPU_CODE", "CODE_ARTICLE"],
    "niveau": ["NIVEAU", "ETAGE", "LEVEL"],
    "batiment": ["BATIMENT", "BAT", "BUILDING", "BLOC"],
    "appart": ["APPART", "APPARTEMENT", "LOGEMENT"],
    "piece": ["PIECE", "ROOM", "ESPACE", "ZONE", "ZONE_PIECE", "LOCAL_PIECE"],
    "type_zone": ["TYPE_ZONE", "TYPE PIECE", "TYPE LOCAL"],
    "formule": ["FORMULE", "FORMULA", "CALCUL"],
    "bim_object_id": ["BIM_OBJECT_ID", "ID_OBJET_BIM", "BIM_ID"],
    "ifc_guid": ["IFC_GUID", "GUID_IFC", "GLOBALID", "GLOBAL_ID"],
    "type_objet": ["TYPE_OBJET", "OBJECT_TYPE", "TYPE_BIM"],
    "famille_bim": ["FAMILLE_BIM", "BIM_FAMILY", "REVIT_FAMILY"],
    "systeme": ["SYSTEME", "SYSTEM", "MEP_SYSTEM"],
    "phase_chantier": ["PHASE_CHANTIER", "PHASE"],
    "altitude": ["ALTITUDE", "ALTIMETRIE", "COTE", "NIVEAU_ALTITUDE"],
    "execution_status": ["EXECUTION_STATUS", "STATUT_EXECUTION", "ETAT_EXECUTION", "REMAINING_WORK_STATUS"],
    "workflow_status": ["WORKFLOW_STATUS", "STATUT_WORKFLOW", "ETAT_WORKFLOW"],
    "eta": ["ETA", "DATE_LIVRAISON", "DATE_POSE", "ECHEANCE"],
    "risque": ["RISQUE", "RISK", "RISK_LEVEL", "NIVEAU_RISQUE"],
    "fournisseur": ["FOURNISSEUR", "SUPPLIER", "VENDOR"],
    "import_local": ["IMPORT_LOCAL", "DECISION_IMPORT", "MODE_ACHAT", "PURCHASE_MODE"],
    "classification": ["CLASSIFICATION", "CLASSEMENT"],
    "omniclass": ["OMNICLASS"],
    "uniclass": ["UNICLASS"],
    "ifc_type": ["IFC_TYPE", "IFCTYPE", "IFC_CLASS"],
    "article_id": ["ARTICLE_ID", "ID_ARTICLE"],
    "bim_object": ["BIM_OBJECT", "OBJET_BIM", "IFC_OBJECT"],
    "decision": ["DECISION", "DECISION_IMPORT", "MODE_ACHAT"],
    "bim_maturity": ["BIM_MATURITY", "MATURITE_BIM", "BIM_MODE"],
}

FIELD_LABELS = {
    "designation": "Designation",
    "quantity": "Quantite",
    "unit": "Unite",
    "local_unit_price": "Prix unitaire local",
    "local_total_amount": "Montant local",
    "import_unit_price": "Prix unitaire import",
    "import_total_amount": "Montant import",
    "lot": "Lot",
    "sous_lot": "Sous-lot",
    "family": "Famille",
    "code_bpu": "Code BPU",
    "niveau": "Niveau",
    "batiment": "Batiment",
    "appart": "Appartement",
    "piece": "Piece",
    "type_zone": "Type de zone",
    "formule": "Formule",
    "bim_object_id": "Objet BIM",
    "ifc_guid": "IFC GUID",
    "type_objet": "Type objet",
    "famille_bim": "Famille BIM",
    "systeme": "Systeme",
    "phase_chantier": "Phase chantier",
    "altitude": "Altitude",
    "execution_status": "Statut execution",
    "workflow_status": "Statut workflow",
    "eta": "ETA",
    "risque": "Risque",
    "fournisseur": "Fournisseur",
    "import_local": "Import/local",
    "classification": "Classification",
    "omniclass": "OmniClass",
    "uniclass": "UniClass",
    "ifc_type": "IFC type",
    "article_id": "Article ID",
    "bim_object": "Objet BIM",
    "decision": "Decision achat",
    "bim_maturity": "Maturite BIM",
}

STANDARD_TO_PUBLIC_FIELD = {
    "designation": "designation",
    "quantite": "quantity",
    "unite": "unit",
    "prix_unitaire_ht": "local_unit_price",
    "prix_total_ht": "local_total_amount",
    "pu_import": "import_unit_price",
    "montant_import": "import_total_amount",
    "lot": "lot",
    "sous_lot": "sous_lot",
    "famille": "family",
    "niveau": "niveau",
    "batiment": "batiment",
    "id_ligne": "code_bpu",
    "appart": "appart",
    "piece": "piece",
    "type_zone": "type_zone",
    "formule": "formule",
    "bim_object_id": "bim_object_id",
    "ifc_guid": "ifc_guid",
    "type_objet": "type_objet",
    "famille_bim": "famille_bim",
    "systeme": "systeme",
    "phase_chantier": "phase_chantier",
    "altitude": "altitude",
    "execution_status": "execution_status",
    "workflow_status": "workflow_status",
    "eta": "eta",
    "risque": "risque",
    "fournisseur": "fournisseur",
    "import_local": "import_local",
    "classification": "classification",
    "omniclass": "omniclass",
    "uniclass": "uniclass",
    "ifc_type": "ifc_type",
    "article_id": "article_id",
    "bim_object": "bim_object",
    "decision": "decision",
    "bim_maturity": "bim_maturity",
}

REQUIRED_GROUPS = (
    ("designation", {"designation"}),
    ("quantity", {"quantity"}),
    ("price_or_amount", {"local_unit_price", "local_total_amount", "import_unit_price", "import_total_amount"}),
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
