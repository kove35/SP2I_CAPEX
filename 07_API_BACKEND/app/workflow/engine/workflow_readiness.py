from __future__ import annotations

from app.workflow.schemas.workflow import WorkflowReadiness


def compute_readiness(workflow_state: str, metrics) -> WorkflowReadiness:
    if workflow_state == "OUT_OF_SYNC":
        return WorkflowReadiness(
            procurement="BLOCKED",
            logistics="BLOCKED",
            execution="BLOCKED",
            chantier="AT_RISK",
            dependencies_critical=1,
        )

    procurement = "READY" if workflow_state in {
        "PROCUREMENT_VALIDATED",
        "ORDER_READY",
        "ORDERED",
        "IN_TRANSIT",
        "RECEIVED",
        "CHANTIER_READY",
        "EXECUTION_IN_PROGRESS",
        "EXECUTION_COMPLETED",
    } else "PARTIAL" if metrics.validated_lines > 0 else "BLOCKED"

    logistics = "READY" if workflow_state in {"RECEIVED", "CHANTIER_READY", "EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"} else (
        "PARTIAL" if workflow_state in {"ORDERED", "IN_TRANSIT"} or metrics.containers > 0 else "BLOCKED"
    )

    execution = "READY" if workflow_state in {"CHANTIER_READY", "EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"} else (
        "PARTIAL" if metrics.execution_actions > 0 else "BLOCKED"
    )

    chantier = "READY" if workflow_state in {"CHANTIER_READY", "EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"} else (
        "AT_RISK" if metrics.execution_blocked or metrics.execution_at_risk else execution
    )

    return WorkflowReadiness(
        procurement=procurement,
        logistics=logistics,
        execution=execution,
        chantier=chantier,
        dependencies_critical=metrics.execution_blocked + metrics.execution_at_risk,
    )
