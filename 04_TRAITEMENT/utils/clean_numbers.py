from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def nettoyer_nombre(valeur: Any, defaut: float | None = None) -> float | None:
    """Convertit une valeur DQE heterogene en float fiable."""
    if valeur is None or valeur == "":
        return defaut

    texte = str(valeur).strip()
    if not texte:
        return defaut

    texte = (
        texte.replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
        .replace("XAF", "")
        .replace("FCFA", "")
    )

    try:
        return float(Decimal(texte))
    except (InvalidOperation, ValueError):
        return defaut


def arrondir_montant(valeur: Any, precision: int = 2) -> float:
    nombre = nettoyer_nombre(valeur, 0) or 0
    return round(nombre, precision)
