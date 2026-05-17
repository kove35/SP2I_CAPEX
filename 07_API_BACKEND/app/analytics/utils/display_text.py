from __future__ import annotations

import re
from typing import Any


LOT_LABELS = {
    1: "L01 - GROS OEUVRE ET DEMOLITION",
    2: "L02 - ETANCHEITE",
    3: "L03 - REVETEMENT DURS",
    4: "L04 - MENUISERIE ALUMINIUM ET VITRERIE",
    5: "L05 - MENUISERIE METALLIQUE ET FERRONNERIE",
    6: "L06 - MENUISERIE BOIS",
    7: "L07 - ELECTRICITE",
    8: "L08 - CLIMATISATION",
    9: "L09 - SECURITE INCENDIE ET VIDEO SURVEILLANCE",
    10: "L10 - PLOMBERIE SANITAIRE",
    11: "L11 - FAUX PLAFOND ET CLOISONS BA13",
    12: "L12 - ASCENSEUR",
    13: "L13 - ALUCOBOND",
    14: "L14 - PEINTURE",
}


ENCODING_REPLACEMENTS = (
    ("?uvre", "oeuvre"),
    ("?UVRE", "OEUVRE"),
    ("ŒUVRE", "OEUVRE"),
    ("œuvre", "oeuvre"),
    ("D?molition", "Demolition"),
    ("D?MOLITION", "DEMOLITION"),
    ("?LECTRICIT?", "ELECTRICITE"),
    ("?lectricit?", "electricite"),
    ("?lectricite", "electricite"),
    ("?TANCH?IT?", "ETANCHEITE"),
    ("?tanch?it?", "etancheite"),
    ("?tanche", "etanche"),
    ("REV?TEMENT", "REVETEMENT"),
    ("Rev?tement", "Revetement"),
    ("rev?tement", "revetement"),
    ("S?CURIT?", "SECURITE"),
    ("S?curit?", "Securite"),
    ("s?curit?", "securite"),
    ("M?TALLIQUE", "METALLIQUE"),
    ("M?tallique", "Metallique"),
    ("m?tallique", "metallique"),
    ("fa?ade", "facade"),
    ("Fa?ade", "Facade"),
    ("FA?ADE", "FACADE"),
    ("acrot?re", "acrotere"),
    ("Acrot?re", "Acrotere"),
    ("gr?s", "gres"),
    ("Gr?s", "Gres"),
    ("r?seau", "reseau"),
    ("R?seau", "Reseau"),
    ("?lectrog?ne", "electrogene"),
    ("?lectrogene", "electrogene"),
    ("?lectrique", "electrique"),
    ("?clairage", "eclairage"),
    ("?clairages", "eclairages"),
    ("encastr?", "encastre"),
    ("Encastr?", "Encastre"),
    ("antid?rapant", "antiderapant"),
    ("Antid?rapant", "Antiderapant"),
    ("c?rame", "cerame"),
    ("C?rame", "Cerame"),
    ("Fa?ence", "Faience"),
    ("fa?ence", "faience"),
    ("travers?e", "traversee"),
    ("Relev?", "Releve"),
    ("relev?", "releve"),
    ("p?riph?rique", "peripherique"),
    ("Unit?", "Unite"),
    ("unit?", "unite"),
    ("int?rieure", "interieure"),
    ("ext?rieure", "exterieure"),
    ("galvanis?e", "galvanisee"),
    ("galvanis?", "galvanise"),
    ("m?dical", "medical"),
    ("d?montable", "demontable"),
    ("retomb?e", "retombee"),
    ("d?corative", "decorative"),
    ("Signal?tique", "Signaletique"),
    ("signal?tique", "signaletique"),
    ("arr?ts", "arrets"),
    ("accessibilit?", "accessibilite"),
    ("thermolaqu?", "thermolaque"),
    ("Vid?o", "Video"),
    ("vid?o", "video"),
    ("M?DICAL", "MEDICAL"),
    ("M?dical", "Medical"),
)

LOT_PATTERN = re.compile(r"\bL(?:OT)?\s*0?(\d{1,2})\b", re.IGNORECASE)


def normalize_display_text(value: Any) -> Any:
    """
    Nettoie les libelles avant affichage frontend/Power BI-like.

    Cette fonction ne modifie pas les montants ni la logique metier : elle corrige
    uniquement les libelles deja corrompus par un export ou une generation Excel
    qui a remplace certains caracteres francais par `?`.
    """
    if not isinstance(value, str):
        return value

    text_value = value
    for source, target in ENCODING_REPLACEMENTS:
        text_value = text_value.replace(source, target)
    text_value = text_value.replace("?", "e")

    match = LOT_PATTERN.search(text_value)
    if match:
        lot_number = int(match.group(1))
        if lot_number in LOT_LABELS:
            return LOT_LABELS[lot_number]

    return text_value


def normalize_payload_labels(value: Any) -> Any:
    """Applique le nettoyage de libelles sur un payload JSON complet."""
    if isinstance(value, dict):
        return {key: normalize_payload_labels(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_payload_labels(item) for item in value]
    return normalize_display_text(value)
