from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


WorkflowTimelineStatus = Literal["done", "active", "waiting", "blocked", "risk"]


class WorkflowAction(BaseModel):
    label: str
    route: str = ""
    type: str = "navigate"
    reason: str = ""


class WorkflowBlocker(BaseModel):
    code: str
    label: str
    severity: Literal["info", "warning", "critical"] = "warning"
    module: str = ""


class WorkflowAlert(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "critical"] = "info"
    module: str = ""


class WorkflowTimelineItem(BaseModel):
    id: str
    label: str
    state: WorkflowTimelineStatus
    status: str = ""
    progress: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)


class WorkflowReadiness(BaseModel):
    procurement: str = "BLOCKED"
    logistics: str = "BLOCKED"
    execution: str = "BLOCKED"
    chantier: str = "BLOCKED"
    dependencies_critical: int = 0


class WorkflowMetrics(BaseModel):
    progress_percent: int = 0
    validated_lines: int = 0
    pending_lines: int = 0
    to_arbitrate: int = 0
    orders: int = 0
    containers: int = 0
    eta_average_days: int = 0
    execution_actions: int = 0
    execution_blocked: int = 0
    execution_at_risk: int = 0
    simulation_lines: int = 0
    dqe_lines: int = 0
    capex_local_total: float = 0
    latest_dqe_certification: datetime | None = None
    latest_fact_metre_sync: datetime | None = None
    dqe_sync_status: str = "OUT_OF_SYNC"
    dqe_sync_delta_rows: int = 0
    dqe_sync_delta_capex: float = 0


class WorkflowState(BaseModel):
    project_id: int
    workflow_state: str = "CONFIGURATION"
    active_step: str = "CONFIGURATION"
    next_action: WorkflowAction = Field(default_factory=lambda: WorkflowAction(label="Configurer le projet", route="/app/projects"))
    progress_percent: int = 0
    procurement_state: str = "BLOCKED"
    approval_state: str = "NOT_REQUIRED"
    logistics_state: str = "BLOCKED"
    execution_state: str = "BLOCKED"
    readiness: WorkflowReadiness = Field(default_factory=WorkflowReadiness)
    blockers: list[WorkflowBlocker] = Field(default_factory=list)
    alerts: list[WorkflowAlert] = Field(default_factory=list)
    timeline: list[WorkflowTimelineItem] = Field(default_factory=list)
    metrics: WorkflowMetrics = Field(default_factory=WorkflowMetrics)
    transitions: list[str] = Field(default_factory=list)
    source: str = "workflow_state_engine"

    # Legacy compatibility for /projects/{id}/workflow-state.
    setup: str = "A_COMPLETER"
    dqe: str = "A_IMPORTER"
    budget: str = "A_SYNCHRONISER"
    scenarios: str = "A_SIMULER"
    procurement: str = "BLOQUE"
    execution: str = "BLOQUEE"
    trust_score: int = 0
    normalized_lines_count: int = 0
    capex_local_total: float = 0
    dqe_synced: bool = False
    last_dqe_certification: datetime | None = None
    last_fact_metre_sync: datetime | None = None
    sync_status: str = "OUT_OF_SYNC"
    sync_delta_rows: int = 0
    sync_delta_capex: float = 0
    counts: dict[str, int] = Field(default_factory=dict)
    file_name: str = ""
