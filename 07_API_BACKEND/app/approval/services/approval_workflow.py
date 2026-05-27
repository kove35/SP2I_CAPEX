from __future__ import annotations


APPROVAL_STATUSES = {
    "PENDING",
    "UNDER_REVIEW",
    "VALIDATION_PROCUREMENT",
    "VALIDATION_TECHNIQUE",
    "VALIDATION_DIRECTION",
    "VALIDATION_FINANCE",
    "APPROVED",
    "REJECTED",
    "ESCALATED",
    "CANCELLED",
    "EXPIRED",
}

TERMINAL_STATUSES = {"APPROVED", "REJECTED", "CANCELLED", "EXPIRED"}

ALLOWED_TRANSITIONS = {
    "PENDING": {"UNDER_REVIEW", "VALIDATION_PROCUREMENT", "VALIDATION_TECHNIQUE", "VALIDATION_DIRECTION", "VALIDATION_FINANCE", "ESCALATED", "CANCELLED", "EXPIRED"},
    "UNDER_REVIEW": {"VALIDATION_PROCUREMENT", "VALIDATION_TECHNIQUE", "VALIDATION_DIRECTION", "VALIDATION_FINANCE", "APPROVED", "REJECTED", "ESCALATED", "CANCELLED", "EXPIRED"},
    "VALIDATION_PROCUREMENT": {"VALIDATION_TECHNIQUE", "VALIDATION_DIRECTION", "VALIDATION_FINANCE", "APPROVED", "REJECTED", "ESCALATED", "CANCELLED", "EXPIRED"},
    "VALIDATION_TECHNIQUE": {"VALIDATION_DIRECTION", "VALIDATION_FINANCE", "APPROVED", "REJECTED", "ESCALATED", "CANCELLED", "EXPIRED"},
    "VALIDATION_DIRECTION": {"VALIDATION_FINANCE", "APPROVED", "REJECTED", "ESCALATED", "CANCELLED", "EXPIRED"},
    "VALIDATION_FINANCE": {"VALIDATION_DIRECTION", "APPROVED", "REJECTED", "ESCALATED", "CANCELLED", "EXPIRED"},
    "ESCALATED": {"VALIDATION_DIRECTION", "VALIDATION_FINANCE", "APPROVED", "REJECTED", "CANCELLED", "EXPIRED"},
    "APPROVED": set(),
    "REJECTED": set(),
    "CANCELLED": set(),
    "EXPIRED": set(),
}


def normalize_status(value: str | None) -> str:
    status = str(value or "").strip().upper()
    return status if status in APPROVAL_STATUSES else "PENDING"


def assert_transition_allowed(previous_status: str, next_status: str) -> None:
    previous = normalize_status(previous_status)
    next_value = normalize_status(next_status)
    if previous == next_value:
        return
    if next_value not in ALLOWED_TRANSITIONS.get(previous, set()):
        raise ValueError(f"Transition approval interdite: {previous} -> {next_value}")
