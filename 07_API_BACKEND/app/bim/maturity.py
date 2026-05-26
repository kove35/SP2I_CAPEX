from __future__ import annotations

import unicodedata
import re
from typing import Any


BIM_MATURITY_NON_BIM = "NON_BIM"
BIM_MATURITY_LITE = "BIM_LITE"
BIM_MATURITY_READY = "BIM_READY"

SPATIAL_FIELDS = {
    "batiment": {"batiment", "bat", "building", "bloc", "immeuble"},
    "niveau": {"niveau", "etage", "level", "floor"},
    "appart": {"appart", "appartement", "logement", "unit_appart"},
    "piece": {"piece", "room", "zone", "espace", "zone_piece", "local_piece"},
    "type_zone": {"type_zone", "zone_type", "type_piece"},
    "sous_lot": {"sous_lot", "souslot", "sub_lot", "sub_trade"},
}

BIM_FIELDS = {
    "bim_object_id": {"bim_object_id", "object_id", "id_objet_bim", "bim_id"},
    "ifc_guid": {"ifc_guid", "guid_ifc", "global_id", "globalid"},
    "type_objet": {"type_objet", "object_type", "type_bim", "type"},
    "famille_bim": {"famille_bim", "bim_family", "revit_family", "famille_revit"},
    "systeme": {"systeme", "system", "mep_system"},
    "phase_chantier": {"phase_chantier", "phase", "work_phase"},
    "classification": {"classification", "classement", "class"},
    "omniclass": {"omniclass"},
    "uniclass": {"uniclass"},
    "ifc_type": {"ifc_type", "ifctype", "ifc_class"},
}


def normalize_label(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def detect_bim_maturity_from_columns(columns: list[Any]) -> dict[str, Any]:
    normalized_columns = {normalize_label(column): str(column) for column in columns if column not in (None, "")}
    spatial = _detect_fields(normalized_columns, SPATIAL_FIELDS)
    bim = _detect_fields(normalized_columns, BIM_FIELDS)
    spatial_without_lot = set(spatial)
    strong_bim_fields = {"bim_object_id", "ifc_guid", "type_objet", "ifc_type"} & set(bim)

    if strong_bim_fields or len(bim) >= 2:
        maturity = BIM_MATURITY_READY
    elif spatial_without_lot:
        maturity = BIM_MATURITY_LITE
    else:
        maturity = BIM_MATURITY_NON_BIM

    confidence = _confidence(maturity, len(spatial), len(bim))
    return {
        "maturity": maturity,
        "mode": maturity,
        "is_bim_compatible": maturity in {BIM_MATURITY_LITE, BIM_MATURITY_READY},
        "spatial_fields": spatial,
        "bim_fields": bim,
        "available_columns": list(normalized_columns.values()),
        "confidence": confidence,
        "capabilities": _capabilities(maturity, spatial, bim),
    }


def enrich_bim_maturity_with_lines(maturity: dict[str, Any], lines: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(lines)
    spatial_keys = ["batiment", "niveau", "appart", "piece", "type_zone", "sous_lot"]
    bim_keys = ["bim_object_id", "ifc_guid", "type_objet", "famille_bim", "systeme", "phase_chantier", "classification", "omniclass", "uniclass", "ifc_type"]
    coverage = {
        key: _coverage(lines, key)
        for key in [*spatial_keys, *bim_keys]
    }
    spatialized_lines = sum(1 for line in lines if any(str(line.get(key) or "").strip() for key in spatial_keys))
    bim_object_lines = sum(1 for line in lines if any(str(line.get(key) or "").strip() for key in ("bim_object_id", "ifc_guid")))
    return {
        **maturity,
        "line_count": total,
        "spatialized_lines_count": spatialized_lines,
        "bim_object_lines_count": bim_object_lines,
        "coverage": coverage,
    }


def _detect_fields(normalized_columns: dict[str, str], aliases: dict[str, set[str]]) -> dict[str, str]:
    detected: dict[str, str] = {}
    for field, names in aliases.items():
        normalized_aliases = {normalize_label(alias) for alias in names}
        match = next((column for column in normalized_columns if column in normalized_aliases), "")
        if match:
            detected[field] = normalized_columns[match]
    return detected


def _coverage(lines: list[dict[str, Any]], key: str) -> float:
    if not lines:
        return 0.0
    filled = sum(1 for line in lines if str(line.get(key) or "").strip())
    return round(filled / len(lines), 4)


def _confidence(maturity: str, spatial_count: int, bim_count: int) -> int:
    if maturity == BIM_MATURITY_READY:
        return min(96, 72 + bim_count * 8 + spatial_count * 3)
    if maturity == BIM_MATURITY_LITE:
        return min(88, 58 + spatial_count * 10)
    return 100


def _capabilities(maturity: str, spatial: dict[str, str], bim: dict[str, str]) -> list[str]:
    capabilities = ["CAPEX_LOT"]
    if maturity in {BIM_MATURITY_LITE, BIM_MATURITY_READY}:
        if "batiment" in spatial:
            capabilities.append("CAPEX_PAR_BATIMENT")
        if "niveau" in spatial:
            capabilities.append("CAPEX_PAR_NIVEAU")
        if "piece" in spatial or "appart" in spatial:
            capabilities.append("CAPEX_PAR_ZONE")
    if maturity == BIM_MATURITY_READY:
        capabilities.extend(["CAPEX_PAR_OBJET_BIM", "EXECUTION_PAR_OBJET_BIM"])
        if "ifc_guid" in bim:
            capabilities.append("IFC_LINK_READY")
    return capabilities
