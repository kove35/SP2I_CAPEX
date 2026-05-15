from __future__ import annotations

"""Parametres logistiques par defaut pour Chine -> Pointe-Noire."""

CONTAINERS = {
    "20FT": {"max_volume": 33.0, "max_weight": 28000.0, "container_cost": 6500.0},
    "40FT": {"max_volume": 67.0, "max_weight": 26500.0, "container_cost": 12000.0},
    "40HC": {"max_volume": 76.0, "max_weight": 26500.0, "container_cost": 13500.0},
}

LCL_COST_PER_CBM = 260.0
FCL_FILL_RATE_THRESHOLD = 0.55

DEFAULT_DEPARTURE_PORT = "Shanghai"
DEFAULT_ARRIVAL_PORT = "Pointe-Noire"
DEFAULT_PORT_COST_RATE = 0.08
DEFAULT_CUSTOMS_RATE = 0.12
DEFAULT_INSURANCE_RATE = 0.015
DEFAULT_LOCAL_DELIVERY_RATE = 0.035
DEFAULT_STORAGE_COST_PER_CBM_DAY = 2.5
DEFAULT_SITE_STORAGE_CAPACITY_CBM = 120.0
DEFAULT_SITE_STORAGE_DAYS = 5

SHIPMENT_STATUS_DAYS_REMAINING = {
    "READY": 80,
    "IN_PRODUCTION": 70,
    "AT_PORT": 55,
    "ON_VESSEL": 45,
    "AT_SEA": 18,
    "AT_CUSTOMS": 7,
    "DELIVERED": 2,
    "ON_SITE": 0,
}
