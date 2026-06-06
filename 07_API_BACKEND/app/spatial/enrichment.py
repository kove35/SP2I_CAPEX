from __future__ import annotations

import re
import unicodedata
from typing import Any


PIECE_TYPE_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("SEJOUR", "SALON", "CUISINE"), "JOUR"),
    (("CHAMBRE", "DRESSING"), "NUIT"),
    (("SDE", "SALLE_DEAU", "SALLE_D_EAU", "SDB", "SALLE_DE_BAIN", "WC"), "SANITAIRE"),
    (("COULOIR", "ESCALIER"), "CIRCULATION"),
    (("BALCON", "TERRASSE"), "EXTERIEUR"),
)


def infer_piece_type(piece_name: Any) -> str:
    """Infer a lightweight PLAN_READY room type from a 2D/DQE room label."""
    normalized = _normalize_piece_label(piece_name)
    if not normalized:
        return "NON_DISPONIBLE"
    for aliases, piece_type in PIECE_TYPE_RULES:
        if any(alias in normalized for alias in aliases):
            return piece_type
    return "AUTRE"


def infer_piece_type_sql(expression: str) -> str:
    upper = f"UPPER(translate(COALESCE({expression}, ''), 'éèêëàâäîïôöùûüçÉÈÊËÀÂÄÎÏÔÖÙÛÜÇ', 'eeeeaaaiioouuucEEEEAAAIIIOOUUUC'))"
    return f"""
        CASE
            WHEN {upper} LIKE '%SEJOUR%' OR {upper} LIKE '%SALON%' OR {upper} LIKE '%CUISINE%' THEN 'JOUR'
            WHEN {upper} LIKE '%CHAMBRE%' OR {upper} LIKE '%DRESSING%' THEN 'NUIT'
            WHEN {upper} LIKE '%SDE%' OR {upper} LIKE '%SALLE_DEAU%' OR {upper} LIKE '%SALLE D EAU%' OR {upper} LIKE '%SDB%' OR {upper} LIKE '%SALLE DE BAIN%' OR {upper} LIKE '%WC%' THEN 'SANITAIRE'
            WHEN {upper} LIKE '%COULOIR%' OR {upper} LIKE '%ESCALIER%' THEN 'CIRCULATION'
            WHEN {upper} LIKE '%BALCON%' OR {upper} LIKE '%TERRASSE%' THEN 'EXTERIEUR'
            ELSE 'AUTRE'
        END
    """


def _normalize_piece_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^A-Z0-9]+", "_", text).strip("_")
