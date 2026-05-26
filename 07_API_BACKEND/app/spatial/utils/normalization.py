from __future__ import annotations

from typing import Any

from app.utils.id_normalizer import normalize_id


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
    return " / ".join(normalize_id(part) for part in parts if normalize_id(part))
