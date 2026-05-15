from __future__ import annotations

"""
Parametres procurement par defaut.

Ces valeurs representent un scenario prudent Chine -> Pointe-Noire. Elles sont
centralisees pour eviter de disperser des hypotheses logistiques dans le code.
"""

DEFAULT_SUPPLIER_PRODUCTION_DAYS = 15
DEFAULT_SEA_FREIGHT_DAYS_CHINA_TO_POINTE_NOIRE = 45
DEFAULT_CONGO_CUSTOMS_DAYS = 7
DEFAULT_LOCAL_TRANSPORT_DAYS = 3
DEFAULT_SECURITY_BUFFER_DAYS = 10

DEFAULT_ADVANCE_PAYMENT_RATE = 0.30
DEFAULT_REMAINING_PAYMENT_RATE = 0.70
DEFAULT_CASHFLOW_TENSION = "MEDIUM"

RISK_WEIGHTS = {
    "supplier": 0.30,
    "country": 0.25,
    "logistics": 0.25,
    "project": 0.20,
}

DEFAULT_COUNTRY_RISKS = {
    "customs_risk": 55,
    "port_risk": 50,
    "logistics_risk": 45,
    "currency_risk": 35,
    "political_risk": 35,
}

PRODUCT_COMPLEXITY_DEFAULTS = {
    "peinture": 25,
    "carrelage": 30,
    "luminaire": 45,
    "menuiserie": 50,
    "groupe electrogene": 75,
    "ascenseur": 85,
    "irm": 95,
}

CRITICALITY_RISK = {
    "LOW": 15,
    "MEDIUM": 40,
    "HIGH": 70,
    "CRITICAL": 90,
}
