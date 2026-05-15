from __future__ import annotations

"""
Parametres globaux du moteur CAPEX.

Ce fichier devient la source de verite des constantes metier utilisees par le
moteur. Les valeurs pourront plus tard venir de PostgreSQL ou d'un ecran
d'administration, mais le code applicatif doit deja eviter les magic numbers.
"""

DEFAULT_TAUX_TRANSPORT = 0.15
DEFAULT_TAUX_ASSURANCE = 0.02
DEFAULT_TAUX_DOUANE = 0.20
DEFAULT_TAUX_FRAIS_PORTUAIRES = 0.10
DEFAULT_TAUX_LOGISTIQUE_LOCALE = 0.05

DEFAULT_SEUIL_DECISION_IMPORT = 0.97
DEFAULT_COEFFICIENT_RISQUE = 1.10

DEFAULT_SIMULATION_MODE = "tolerant"

DEFAULT_TAUX_LANDED_COST = {
    "transport_maritime": DEFAULT_TAUX_TRANSPORT,
    "assurance": DEFAULT_TAUX_ASSURANCE,
    "droits_douane": DEFAULT_TAUX_DOUANE,
    "frais_portuaires": DEFAULT_TAUX_FRAIS_PORTUAIRES,
    "logistique_locale": DEFAULT_TAUX_LOGISTIQUE_LOCALE,
}

DEFAULT_RATIOS_FOB = {
    "alucobond": 0.6,
    "ascenseur": 0.8,
    "climatisation": 0.7,
    "electricite": 0.5,
    "gros_oeuvre": 0.55,
    "menuiserie": 0.6,
    "peinture": 0.5,
    "plomberie": 0.5,
    "default": 0.5,
}

VALID_SIMULATION_MODES = {"strict", "tolerant"}
