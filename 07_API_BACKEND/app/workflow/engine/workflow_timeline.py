from __future__ import annotations

from app.workflow.schemas.workflow import WorkflowTimelineItem


TIMELINE = [
    ("simulation", "Simulation", {"SIMULATION_READY", "SIMULATION_COMPLETED"}),
    ("arbitrage", "Arbitrage", {"ARBITRAGE_IN_PROGRESS", "ARBITRAGE_COMPLETED"}),
    ("validation", "Validation", {"PROCUREMENT_VALIDATED"}),
    ("commande", "Commande", {"ORDER_READY", "ORDERED"}),
    ("transport", "Transport", {"IN_TRANSIT"}),
    ("reception", "Reception", {"RECEIVED"}),
    ("preparation_chantier", "Preparation chantier", {"CHANTIER_READY"}),
    ("execution", "Execution", {"EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"}),
]

STATE_ORDER = [
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
]


def _index(state: str) -> int:
    try:
        return STATE_ORDER.index(state)
    except ValueError:
        return 0


def compute_timeline(workflow_state: str, metrics, blockers) -> list[WorkflowTimelineItem]:
    current = _index(workflow_state)
    items: list[WorkflowTimelineItem] = []
    for item_id, label, active_states in TIMELINE:
        active_index = min(_index(state) for state in active_states)
        end_index = max(_index(state) for state in active_states)
        if current > end_index:
            state = "done"
        elif workflow_state in active_states or (active_index <= current <= end_index):
            state = "risk" if blockers else "active"
        else:
            state = "waiting" if current < active_index else "done"
        item_metrics = {}
        if item_id == "arbitrage":
            item_metrics = {"validated_lines": metrics.validated_lines, "pending_lines": metrics.pending_lines}
        elif item_id == "commande":
            item_metrics = {"orders": metrics.orders}
        elif item_id == "transport":
            item_metrics = {"eta_average_days": metrics.eta_average_days, "containers": metrics.containers}
        elif item_id == "execution":
            item_metrics = {"actions": metrics.execution_actions, "blocked": metrics.execution_blocked}
        items.append(WorkflowTimelineItem(id=item_id, label=label, state=state, metrics=item_metrics))
    return items
