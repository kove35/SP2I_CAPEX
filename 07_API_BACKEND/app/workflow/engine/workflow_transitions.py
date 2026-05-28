from __future__ import annotations


WORKFLOW_STATES = (
    "CONFIGURATION",
    "DQE_CERTIFIED",
    "BUDGET_SYNCED",
    "SIMULATION_READY",
    "SIMULATION_COMPLETED",
    "ARBITRAGE_IN_PROGRESS",
    "ARBITRAGE_COMPLETED",
    "PROCUREMENT_VALIDATED",
    "ORDER_READY",
    "ORDERED",
    "IN_TRANSIT",
    "RECEIVED",
    "CHANTIER_READY",
    "EXECUTION_IN_PROGRESS",
    "EXECUTION_COMPLETED",
)


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "CONFIGURATION": {"DQE_CERTIFIED"},
    "DQE_CERTIFIED": {"BUDGET_SYNCED"},
    "BUDGET_SYNCED": {"SIMULATION_READY", "SIMULATION_COMPLETED"},
    "SIMULATION_READY": {"SIMULATION_COMPLETED"},
    "SIMULATION_COMPLETED": {"ARBITRAGE_IN_PROGRESS", "ARBITRAGE_COMPLETED"},
    "ARBITRAGE_IN_PROGRESS": {"ARBITRAGE_COMPLETED"},
    "ARBITRAGE_COMPLETED": {"PROCUREMENT_VALIDATED"},
    "PROCUREMENT_VALIDATED": {"ORDER_READY"},
    "ORDER_READY": {"ORDERED"},
    "ORDERED": {"IN_TRANSIT"},
    "IN_TRANSIT": {"RECEIVED"},
    "RECEIVED": {"CHANTIER_READY"},
    "CHANTIER_READY": {"EXECUTION_IN_PROGRESS"},
    "EXECUTION_IN_PROGRESS": {"EXECUTION_COMPLETED"},
    "EXECUTION_COMPLETED": set(),
}


EVENT_TARGET_STATES: dict[str, str] = {
    "DQE_CERTIFIED": "DQE_CERTIFIED",
    "BUDGET_SYNCED": "BUDGET_SYNCED",
    "SIMULATION_COMPLETED": "SIMULATION_COMPLETED",
    "PROCUREMENT_LINE_VALIDATED": "ARBITRAGE_IN_PROGRESS",
    "PROCUREMENT_ARBITRAGE_COMPLETED": "ARBITRAGE_COMPLETED",
    "ORDER_CREATED": "ORDER_READY",
    "ORDER_VALIDATED": "ORDERED",
    "CONTAINER_CONFIRMED": "ORDERED",
    "SHIPMENT_STARTED": "IN_TRANSIT",
    "GOODS_RECEIVED": "RECEIVED",
    "CHANTIER_READY": "CHANTIER_READY",
    "EXECUTION_STARTED": "EXECUTION_IN_PROGRESS",
    "EXECUTION_COMPLETED": "EXECUTION_COMPLETED",
}


def can_transition(from_state: str, to_state: str) -> bool:
    if from_state == to_state:
        return True
    return to_state in ALLOWED_TRANSITIONS.get(from_state, set())


def allowed_next_states(from_state: str) -> list[str]:
    return sorted(ALLOWED_TRANSITIONS.get(from_state, set()))


def transition_for_event(event_type: str) -> str | None:
    return EVENT_TARGET_STATES.get(event_type)


def assert_transition(from_state: str, to_state: str) -> None:
    if not can_transition(from_state, to_state):
        raise ValueError(f"Invalid workflow transition: {from_state} -> {to_state}")
