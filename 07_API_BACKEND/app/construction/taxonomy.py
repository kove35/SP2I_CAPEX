from __future__ import annotations

from dataclasses import dataclass


LOTS_PRINCIPAUX = (
    "GROS_OEUVRE",
    "MACONNERIE",
    "ETANCHEITE",
    "CHARPENTE",
    "COUVERTURE",
    "MENUISERIE_ALU",
    "MENUISERIE_BOIS",
    "ELECTRICITE",
    "PLOMBERIE",
    "CLIMATISATION",
    "REVETEMENTS",
    "PEINTURE",
    "FAUX_PLAFONDS",
    "ASCENSEUR",
    "SMART_BUILDING",
    "SECURITE_INCENDIE",
    "VRD",
    "FACADE",
    "ENERGIE_SOLAIRE",
)


@dataclass(frozen=True)
class SousLotDefinition:
    lot: str
    code: str
    label: str


SOUS_LOTS_METIER = (
    SousLotDefinition("ELECTRICITE", "11.1", "APPAREILS_ECLAIRAGE_NORMAL"),
    SousLotDefinition("ELECTRICITE", "11.2", "ECLAIRAGE_BALISAGE"),
    SousLotDefinition("ELECTRICITE", "11.3", "PRISES_COMMANDES"),
    SousLotDefinition("ELECTRICITE", "11.4", "CABLES_FOURREAUX"),
    SousLotDefinition("ELECTRICITE", "11.5", "TABLEAUX"),
    SousLotDefinition("ELECTRICITE", "11.6", "TERRE"),
    SousLotDefinition("ELECTRICITE", "11.7", "SECOURS"),
    SousLotDefinition("ELECTRICITE", "11.8", "SOLAIRE"),
    SousLotDefinition("ELECTRICITE", "11.9", "CHEMINS_CABLES"),
    SousLotDefinition("ELECTRICITE", "11.10", "SMART_BUILDING"),
    SousLotDefinition("PLOMBERIE", "12.1", "ALIMENTATION_EAU"),
    SousLotDefinition("PLOMBERIE", "12.2", "EVACUATION"),
    SousLotDefinition("PLOMBERIE", "12.3", "APPAREILS_SANITAIRES"),
    SousLotDefinition("CLIMATISATION", "13.1", "GROUPES_EXTERIEURS"),
    SousLotDefinition("CLIMATISATION", "13.2", "RESEAUX_FRIGORIFIQUES"),
    SousLotDefinition("CHARPENTE", "14.1", "CHARPENTE_BOIS"),
    SousLotDefinition("COUVERTURE", "14.2", "BAC_ACIER"),
    SousLotDefinition("FACADE", "15.1", "MENUISERIE_FACADE"),
    SousLotDefinition("VRD", "16.1", "ACCES_CHANTIER"),
    SousLotDefinition("SECURITE_INCENDIE", "17.1", "DETECTION_INCENDIE"),
)


REMAINING_WORK_STATUSES = ("EXISTANT", "EN_COURS", "A_EXECUTER", "TERMINE", "EXPLOITE")

SITE_OCCUPE_RISK_TYPES = (
    "NUISANCES",
    "ACCES",
    "SECURITE_CLIENTS",
    "CIRCULATION_CHANTIER",
    "COACTIVITE",
    "PROTECTION_INFILTRATION",
)


def validate_taxonomy() -> list[str]:
    errors: list[str] = []
    lots = set(LOTS_PRINCIPAUX)
    if not lots:
        errors.append("LOTS_PRINCIPAUX is empty")
    for item in SOUS_LOTS_METIER:
        if item.lot not in lots:
            errors.append(f"Sous-lot {item.code} references unknown lot {item.lot}")
        if not item.code or not item.label:
            errors.append(f"Sous-lot definition is incomplete: {item!r}")
    for status in REMAINING_WORK_STATUSES:
        if not status:
            errors.append("Remaining work status cannot be empty")
    return errors
