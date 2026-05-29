from __future__ import annotations

from typing import Any

from app.workflow.engine.workflow_transitions import WORKFLOW_STATES
from app.workflow.schemas.workflow import WorkflowMetrics


def _count(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def compute_progress_percent(workflow_state: str) -> int:
    try:
        index = WORKFLOW_STATES.index(workflow_state)
    except ValueError:
        index = 0
    return round((index / max(len(WORKFLOW_STATES) - 1, 1)) * 100)


def compute_workflow_metrics(snapshot: dict[str, Any], workflow_state: str) -> WorkflowMetrics:
    procurement = snapshot.get("procurement") or {}
    execution = snapshot.get("execution") or {}
    base = snapshot.get("base_metrics")
    validated = _count(procurement.get("validated_decisions_count"))
    decisions = _count(procurement.get("decisions_count"))
    pending = _count(procurement.get("pending_decisions_count"))
    to_arbitrate = _count(procurement.get("to_arbitrate_count") or procurement.get("review_required_count"))

    if decisions and not pending and validated < decisions:
        pending = max(decisions - validated, 0)
    if decisions and not to_arbitrate and validated < decisions:
        to_arbitrate = max(decisions - validated, 0)

    return WorkflowMetrics(
        progress_percent=compute_progress_percent(workflow_state),
        validated_lines=validated,
        pending_lines=pending,
        to_arbitrate=to_arbitrate,
        orders=_count(snapshot.get("orders_count")),
        containers=_count(snapshot.get("containers_count")),
        eta_average_days=_count(snapshot.get("eta_average_days")),
        execution_actions=_count(execution.get("actions_count")),
        execution_blocked=_count(execution.get("blocked_count")),
        execution_at_risk=_count(execution.get("at_risk_count")),
        simulation_lines=_count(getattr(base, "simulation_rows", 0)),
        dqe_lines=_count(getattr(base, "fact_metre_rows", 0)),
        capex_local_total=float(getattr(base, "capex_local_total", 0) or 0),
        latest_dqe_certification=getattr(base, "last_dqe_certification", None),
        latest_fact_metre_sync=getattr(base, "last_fact_metre_sync", None),
        dqe_sync_status=str(getattr(base, "sync_status", "OUT_OF_SYNC") or "OUT_OF_SYNC"),
        dqe_sync_delta_rows=_count(getattr(base, "sync_delta_rows", 0)),
        dqe_sync_delta_capex=float(getattr(base, "sync_delta_capex", 0) or 0),
    )
