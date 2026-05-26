from __future__ import annotations

from typing import Any


UNKNOWN_BY_LEVEL = {
    "project": "Projet",
    "batiment": "Bâtiment non renseigné",
    "niveau": "Niveau global",
    "appart": "Appartement non renseigné",
    "piece": "Pièce non renseignée",
    "lot": "Lot non renseigné",
    "objet_bim": "Objet BIM non renseigné",
}


def normalize_spatial_value(value: Any, level: str) -> str:
    text = str(value or "").strip()
    return text if text else UNKNOWN_BY_LEVEL.get(level, "Non renseigné")


def make_spatial_key(*parts: Any) -> str:
    return " / ".join(str(part or "").strip() for part in parts if str(part or "").strip())
