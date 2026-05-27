from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


APPROVAL_TYPES = {
    "PROCUREMENT_ARBITRATION",
    "CAPEX_DECISION",
    "CHANTIER_VALIDATION",
    "SUPPLY_CHAIN_WORKFLOW",
    "DIRECTION_DECISION",
}

RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def normalize_choice(value: Any, allowed: set[str], default: str) -> str:
    candidate = str(value or "").strip().upper()
    return candidate if candidate in allowed else default


def normalize_decision(value: Any) -> str:
    decision = str(value or "").strip().upper()
    if decision in {"VALIDE", "VALIDATED"}:
        return "APPROVED"
    if decision in {"REFUSE", "REFUSED"}:
        return "REJECTED"
    if decision in {"IMPORT", "LOCAL", "HYBRID", "HYBRIDE", "A_ARBITRER", "APPROVED", "REJECTED"}:
        return "HYBRID" if decision == "HYBRIDE" else decision
    return "A_ARBITRER"


def default_deadline(priority: str, risk_level: str) -> datetime:
    urgency = normalize_choice(priority, PRIORITIES, "MEDIUM")
    risk = normalize_choice(risk_level, RISK_LEVELS, "MEDIUM")
    if urgency == "CRITICAL" or risk == "CRITICAL":
        days = 1
    elif urgency == "HIGH" or risk == "HIGH":
        days = 3
    elif urgency == "LOW" and risk == "LOW":
        days = 14
    else:
        days = 7
    return datetime.now(timezone.utc) + timedelta(days=days)


def resolve_required_role(values: dict[str, Any]) -> str:
    approval_type = normalize_choice(values.get("approval_type"), APPROVAL_TYPES, "PROCUREMENT_ARBITRATION")
    risk_level = normalize_choice(values.get("risk_level"), RISK_LEVELS, "MEDIUM")
    estimated_saving = float(values.get("estimated_saving") or 0)
    roi = values.get("roi")
    roi_value = float(roi) if roi is not None else 0

    if approval_type == "DIRECTION_DECISION" or risk_level == "CRITICAL" or estimated_saving >= 50_000_000:
        return "DIRECTION"
    if approval_type == "CAPEX_DECISION" or roi_value >= 20 or estimated_saving >= 10_000_000:
        return "FINANCE"
    if approval_type == "CHANTIER_VALIDATION":
        return "DIRECTION_TRAVAUX"
    if approval_type == "SUPPLY_CHAIN_WORKFLOW":
        return "SUPPLY_CHAIN_MANAGER"
    return "PROCUREMENT_MANAGER"


def initial_status_for_role(role_required: str) -> str:
    role = str(role_required or "").strip().upper()
    if role == "DIRECTION":
        return "VALIDATION_DIRECTION"
    if role == "FINANCE":
        return "VALIDATION_FINANCE"
    if role == "DIRECTION_TRAVAUX":
        return "VALIDATION_TECHNIQUE"
    if role in {"SUPPLY_CHAIN_MANAGER", "PROCUREMENT_MANAGER"}:
        return "VALIDATION_PROCUREMENT"
    return "PENDING"
