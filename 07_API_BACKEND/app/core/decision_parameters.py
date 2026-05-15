from __future__ import annotations

"""
Parametres explicables du DecisionEngine.

Les poids sont centralises ici pour eviter les constantes dispersees. Le score
final est volontairement simple et auditable : chaque composante est visible
dans la reponse API et en base.
"""

WEIGHT_SAVINGS = 0.40
WEIGHT_RISK = 0.25
WEIGHT_LEAD_TIME = 0.20
WEIGHT_CRITICALITY = 0.15

MIN_IMPORT_SCORE = 65
MIN_MIXED_SCORE = 45

HIGH_CONFIDENCE_SCORE = 75
MEDIUM_CONFIDENCE_SCORE = 50

DEFAULT_SUPPLIER_RISK_SCORE = 35
DEFAULT_LOGISTICS_RISK_SCORE = 30
DEFAULT_LEAD_TIME_DAYS = 35
DEFAULT_CRITICALITY = "MEDIUM"

CRITICALITY_WEIGHTS = {
    "LOW": 10,
    "MEDIUM": 35,
    "HIGH": 65,
    "CRITICAL": 90,
}

DECISION_RULES = {
    "IMPORT": "Import recommande : l'economie compense les risques identifies.",
    "LOCAL": "Local recommande : le risque, le delai ou le faible gain ne justifie pas l'import.",
    "MIXTE": "Decision mixte : gain interessant mais conditions a securiser avant arbitrage final.",
}
