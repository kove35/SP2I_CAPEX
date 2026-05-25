from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2)
    client_name: str = ""
    city: str = "Pointe-Noire"
    country: str = "Congo-Brazzaville"
    currency: str = "FCFA"
    status: str = "ACTIVE"
    project_type: str = ""
    project_manager: str = ""


class ProjectSetupUpdate(BaseModel):
    name: str | None = None
    client_name: str | None = None
    city: str | None = None
    country: str | None = None
    currency: str | None = None
    project_type: str | None = None
    project_manager: str | None = None
    target_budget: float | None = None
    vat_mode: str | None = None
    reference_exchange_rate: float | None = None
    default_transport_rate: float | None = None
    default_customs_rate: float | None = None
    default_insurance_rate: float | None = None
    default_import_margin: float | None = None
    minimum_saving_threshold: float | None = None
    planned_start_date: datetime | None = None
    target_delivery_date: datetime | None = None
    site_storage_capacity: float | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    client_name: str
    city: str
    country: str
    currency: str
    project_type: str = ""
    project_manager: str = ""
    target_budget: float | None = None
    vat_mode: str = "HT"
    reference_exchange_rate: float | None = None
    default_transport_rate: float | None = None
    default_customs_rate: float | None = None
    default_insurance_rate: float | None = None
    default_import_margin: float | None = None
    minimum_saving_threshold: float | None = None
    planned_start_date: datetime | None = None
    target_delivery_date: datetime | None = None
    site_storage_capacity: float | None = None
    setup_status: str = "CONFIG_REQUIRED"
    setup_completed_at: datetime | None = None
    owner_id: int
    status: str
    created_at: datetime | None = None
    trust_score: int = 87
    last_dqe: str = "DQE_PROJECT_SP2I.xlsx"
    budget: float = 0


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


class WorkflowStep(BaseModel):
    id: str
    label: str
    status: str
    state: str
    action: str
    route: str


class WorkflowAction(BaseModel):
    label: str
    route: str
    mode: str | None = None


class DqeStatus(BaseModel):
    status: str = "NOT_IMPORTED"
    version_number: int = 0
    file_name: str = ""
    certification_status: str = "UNKNOWN"
    governance_status: str | None = None
    trust_score: int = 0
    normalized_lines_count: int = 0
    ignored_lines_count: int = 0
    data_loss_count: int = 0
    review_required_count: int = 0
    is_active: bool = False
    uploaded_at: datetime | None = None
    analyzed_at: datetime | None = None
    synced_at: datetime | None = None
    issues_summary: dict[str, int] = Field(default_factory=dict)
    issues: list[dict[str, Any]] = Field(default_factory=list)


class BudgetStatus(BaseModel):
    status: str = "SYNC_REQUIRED"
    is_synced: bool = False
    synced_at: datetime | None = None
    lines_count: int = 0
    total_amount: float = 0.0
    source: str = "FACT_METRE"
    message: str = ""


class ScenarioStatus(BaseModel):
    status: str = "NOT_STARTED"
    is_ready: bool = False
    scenario_id: str | None = None
    scenario_name: str | None = None
    scenario_type: str | None = None
    run_id: str | None = None
    run_status: str | None = None
    simulated_at: datetime | None = None
    line_count: int = 0
    source: str = "simulation_run"
    message: str = ""


class ProcurementStatus(BaseModel):
    status: str = "BLOCKED"
    is_ready: bool = False
    decisions_count: int = 0
    import_lines_count: int = 0
    local_lines_count: int = 0
    hybrid_lines_count: int = 0
    validated_decisions_count: int = 0
    pending_decisions_count: int = 0
    to_arbitrate_count: int = 0
    review_required_count: int = 0
    blocked_decisions_count: int = 0
    export_available: bool = False
    source: str = "fact_simulation"
    message: str = ""


class ExecutionStatus(BaseModel):
    status: str = "BLOCKED"
    is_ready: bool = False
    actions_count: int = 0
    open_count: int = 0
    done_count: int = 0
    blocked_count: int = 0
    at_risk_count: int = 0
    critical_lots_count: int = 0
    deliveries_to_watch_count: int = 0
    eta_to_watch_count: int = 0
    source: str = "fact_simulation"
    message: str = ""


class ProjectWorkflowResponse(BaseModel):
    status: str
    label: str
    completion: int
    steps: list[WorkflowStep]
    primary_action: WorkflowAction
    dqe: DqeStatus = Field(default_factory=DqeStatus)
    budget: BudgetStatus = Field(default_factory=BudgetStatus)
    scenario: ScenarioStatus = Field(default_factory=ScenarioStatus)
    procurement: ProcurementStatus = Field(default_factory=ProcurementStatus)
    execution: ExecutionStatus = Field(default_factory=ExecutionStatus)


class ProcurementDecisionBase(BaseModel):
    lot: str = ""
    family: str = ""
    designation: str = ""
    quantity: float = 0
    unit: str = ""
    ai_decision: str = "REVIEW_REQUIRED"
    ai_score: float = 0
    ai_reason: str = ""
    proposed_decision: str = "REVIEW_REQUIRED"
    validated_decision: str = ""
    validation_status: str = "PENDING"
    supplier_selected: str = ""
    supplier_country: str = ""
    purchase_mode: str = ""
    estimated_local_cost: float = 0
    estimated_import_cost: float = 0
    estimated_savings: float = 0
    risk_level: str = "MEDIUM"
    validator_name: str = ""
    validator_id: int | None = None
    validated_at: datetime | None = None
    comment: str = ""


class ProcurementDecisionCreate(ProcurementDecisionBase):
    scenario_id: str | None = None
    simulation_line_id: int | None = None


class ProcurementDecisionUpdate(BaseModel):
    validated_decision: str | None = None
    validation_status: str | None = None
    supplier_selected: str | None = None
    supplier_country: str | None = None
    purchase_mode: str | None = None
    validator_name: str | None = None
    validator_id: int | None = None
    comment: str | None = None


class ProcurementDecisionOut(ProcurementDecisionBase):
    id: int
    project_id: int
    scenario_id: str | None = None
    simulation_line_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProcurementDecisionListResponse(BaseModel):
    decisions: list[ProcurementDecisionOut]


class ProcurementDecisionStatus(BaseModel):
    status: str = "BLOCKED"
    is_ready: bool = False
    decisions_count: int = 0
    validated_decisions_count: int = 0
    pending_decisions_count: int = 0
    to_arbitrate_count: int = 0
    review_required_count: int = 0
    blocked_decisions_count: int = 0
    import_lines_count: int = 0
    local_lines_count: int = 0
    hybrid_lines_count: int = 0
    export_available: bool = False
    source: str = "procurement_decisions"
    message: str = ""


class ProcurementDecisionBootstrapResponse(BaseModel):
    inserted_count: int = 0
    status: ProcurementDecisionStatus = Field(default_factory=ProcurementDecisionStatus)


class SiteExecutionActionBase(BaseModel):
    lot: str = ""
    family: str = ""
    designation: str = ""
    action_type: str = "COORDINATION"
    title: str = ""
    problem: str = ""
    impact: str = ""
    recommended_action: str = ""
    priority: str = "MEDIUM"
    risk_level: str = "MEDIUM"
    status: str = "TO_DO"
    responsible_role: str = ""
    responsible_name: str = ""
    due_date: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    delivery_eta_days: float = 0
    date_needed: datetime | None = None
    delay_days: float = 0
    storage_impact: float = 0
    criticality_score: float = 0
    source: str = "procurement_decisions"


class SiteExecutionActionUpdate(BaseModel):
    status: str | None = None
    responsible_name: str | None = None
    responsible_role: str | None = None
    due_date: datetime | None = None
    recommended_action: str | None = None


class SiteExecutionActionOut(SiteExecutionActionBase):
    id: int
    project_id: int
    scenario_id: str | None = None
    procurement_decision_id: int | None = None
    simulation_line_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SiteExecutionActionListResponse(BaseModel):
    actions: list[SiteExecutionActionOut]


class SiteExecutionActionStatus(BaseModel):
    status: str = "BLOCKED"
    is_ready: bool = False
    actions_count: int = 0
    open_count: int = 0
    done_count: int = 0
    blocked_count: int = 0
    at_risk_count: int = 0
    critical_lots_count: int = 0
    deliveries_to_watch_count: int = 0
    eta_to_watch_count: int = 0
    source: str = "site_execution_actions"
    message: str = ""


class SiteExecutionActionGenerateResponse(BaseModel):
    inserted_count: int = 0
    status: SiteExecutionActionStatus = Field(default_factory=SiteExecutionActionStatus)


class WorkflowEventOut(BaseModel):
    id: int
    project_id: int
    user_id: int | None = None
    event_type: str = ""
    entity_type: str = ""
    entity_id: str = ""
    previous_status: str = ""
    new_status: str = ""
    message: str = ""
    metadata_json: str = "{}"
    created_at: datetime | None = None


class WorkflowEventListResponse(BaseModel):
    events: list[WorkflowEventOut]
