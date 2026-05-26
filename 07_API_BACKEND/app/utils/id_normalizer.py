from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_id(value: Any) -> str:
    """
    Normalise une cle metier Excel sans imposer de semantics BIM.

    Le helper reste volontairement simple et retrocompatible : il stabilise la
    casse, les espaces et les separateurs, mais ne transforme pas un identifiant
    vide en valeur inventee.
    """
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"\s+", "_", text)
    return text.upper()


def normalize_optional_id(value: Any, fallback: Any = "") -> str:
    """Normalise `value`, puis `fallback` si la valeur principale est vide."""
    return normalize_id(value) or normalize_id(fallback)
