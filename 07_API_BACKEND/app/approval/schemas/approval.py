from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


ApprovalStatus = str


class ApprovalBase(BaseModel):
    project_id: int
    simulation_id: str = ""
    procurement_action_id: int | None = None
    article_id: str = ""
    lot_id: str = ""
    sous_lot_id: str = ""
    niveau_id: str = ""
    appartement_id: str = ""
    piece_id: str = ""
    ifc_guid: str = ""
    approval_type: str = "PROCUREMENT_ARBITRATION"
    decision: str = "A_ARBITRER"
    status: ApprovalStatus = "PENDING"
    priority: str = "MEDIUM"
    risk_level: str = "MEDIUM"
    roi: float | None = None
    estimated_saving: float | None = None
    eta: datetime | None = None
    justification_ai: str = ""
    justification_human: str = ""
    requested_by: str = ""
    assigned_to: str = ""
    role_required: str = "PROCUREMENT_MANAGER"
    deadline: datetime | None = None


class ApprovalCreate(ApprovalBase):
    pass


class ApprovalUpdate(BaseModel):
    decision: str | None = None
    status: ApprovalStatus | None = None
    priority: str | None = None
    risk_level: str | None = None
    roi: float | None = None
    estimated_saving: float | None = None
    eta: datetime | None = None
    justification_human: str | None = None
    assigned_to: str | None = None
    role_required: str | None = None
    deadline: datetime | None = None


class ApprovalReviewRequest(BaseModel):
    reviewer: str = ""
    assigned_to: str | None = None
    justification_human: str = ""


class ApprovalDecisionRequest(BaseModel):
    actor: str = ""
    justification_human: str = ""
    decision: str | None = None


class ApprovalOut(ApprovalBase):
    model_config = ConfigDict(from_attributes=True)

    approval_id: int
    approved_by: str = ""
    rejected_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None


class ApprovalListResponse(BaseModel):
    approvals: list[ApprovalOut]


class ApprovalSummary(BaseModel):
    project_id: int
    total_count: int = 0
    pending_count: int = 0
    under_review_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    escalated_count: int = 0
    expired_count: int = 0
    critical_count: int = 0
    estimated_saving_total: float = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_role: dict[str, int] = Field(default_factory=dict)
