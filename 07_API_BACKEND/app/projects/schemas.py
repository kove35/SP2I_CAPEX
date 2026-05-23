from __future__ import annotations

from datetime import datetime

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
    status: str
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


class BudgetStatus(BaseModel):
    status: str


class ProjectWorkflowResponse(BaseModel):
    status: str
    label: str
    completion: int
    steps: list[WorkflowStep]
    primary_action: WorkflowAction
    dqe: DqeStatus = Field(default_factory=DqeStatus)
    budget: BudgetStatus = Field(default_factory=lambda: BudgetStatus(status="SYNC_REQUIRED"))
