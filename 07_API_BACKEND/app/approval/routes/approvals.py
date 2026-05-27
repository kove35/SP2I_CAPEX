from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.approval.repositories.approval_repository import ApprovalRepository
from app.approval.schemas.approval import (
    ApprovalCreate,
    ApprovalDecisionRequest,
    ApprovalListResponse,
    ApprovalOut,
    ApprovalReviewRequest,
    ApprovalSummary,
    ApprovalUpdate,
)
from app.approval.services.approval_engine import ApprovalEngine
from app.approval.services.approval_history import approval_history
from app.approval.services.approval_workflow import APPROVAL_STATUSES, normalize_status
from app.database import get_db


router = APIRouter()


@router.get("/statuses")
def approval_statuses() -> dict[str, list[str]]:
    return {"statuses": sorted(APPROVAL_STATUSES)}


@router.post("", response_model=ApprovalOut)
def create_approval(payload: ApprovalCreate, db: Session = Depends(get_db)) -> ApprovalOut:
    return ApprovalEngine(db).create_approval(payload.model_dump(exclude_unset=True))


@router.get("", response_model=ApprovalListResponse)
def list_approvals(
    project_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    role_required: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ApprovalListResponse:
    repository = ApprovalRepository(db)
    normalized_status = normalize_status(status) if status else None
    approvals = repository.list(project_id=project_id, status=normalized_status, role_required=role_required, limit=limit, offset=offset)
    return ApprovalListResponse(approvals=approvals)


@router.get("/summary/{project_id}", response_model=ApprovalSummary)
def approval_summary(project_id: int, db: Session = Depends(get_db)) -> ApprovalSummary:
    return ApprovalSummary(**ApprovalRepository(db).summary(project_id))


@router.post("/bootstrap/procurement/{project_id}")
def bootstrap_from_procurement(
    project_id: int,
    scenario_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    params: dict[str, object] = {"project_id": project_id}
    scenario_filter = ""
    if scenario_id:
        scenario_filter = "AND pd.scenario_id = :scenario_id"
        params["scenario_id"] = scenario_id

    result = db.execute(
        text(
            f"""
            INSERT INTO fact_approvals (
                project_id,
                simulation_id,
                procurement_action_id,
                article_id,
                lot_id,
                approval_type,
                decision,
                status,
                priority,
                risk_level,
                estimated_saving,
                justification_ai,
                requested_by,
                role_required,
                created_at,
                updated_at,
                deadline
            )
            SELECT
                pd.project_id,
                COALESCE(pd.scenario_id, ''),
                pd.id,
                COALESCE(pd.simulation_line_id::text, ''),
                COALESCE(pd.lot, ''),
                'PROCUREMENT_ARBITRATION',
                COALESCE(NULLIF(pd.proposed_decision, ''), 'A_ARBITRER'),
                CASE
                    WHEN pd.risk_level IN ('HIGH', 'CRITICAL') THEN 'VALIDATION_DIRECTION'
                    WHEN pd.validation_status IN ('TO_ARBITRATE', 'A_ARBITRER', 'VALIDATION_DIRECTION') THEN 'VALIDATION_PROCUREMENT'
                    ELSE 'PENDING'
                END,
                CASE WHEN pd.risk_level IN ('HIGH', 'CRITICAL') THEN 'HIGH' ELSE 'MEDIUM' END,
                COALESCE(NULLIF(pd.risk_level, ''), 'MEDIUM'),
                COALESCE(pd.estimated_savings, 0),
                COALESCE(pd.ai_reason, ''),
                'procurement_decisions',
                CASE WHEN pd.risk_level IN ('HIGH', 'CRITICAL') THEN 'DIRECTION' ELSE 'PROCUREMENT_MANAGER' END,
                now(),
                now(),
                now() + interval '7 days'
            FROM procurement_decisions pd
            WHERE pd.project_id = :project_id
              {scenario_filter}
              AND pd.validation_status IN ('TO_ARBITRATE', 'A_ARBITRER', 'VALIDATION_DIRECTION', 'REVIEW_REQUIRED', 'PENDING')
              AND NOT EXISTS (
                  SELECT 1
                  FROM fact_approvals fa
                  WHERE fa.project_id = pd.project_id
                    AND fa.procurement_action_id = pd.id
              )
            """
        ),
        params,
    )
    inserted = int(result.rowcount or 0)
    db.commit()
    return {"inserted_count": inserted, "project_id": project_id, "scenario_id": scenario_id}


@router.get("/{approval_id}", response_model=ApprovalOut)
def get_approval(approval_id: int, db: Session = Depends(get_db)) -> ApprovalOut:
    approval = ApprovalRepository(db).get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return approval


@router.patch("/{approval_id}", response_model=ApprovalOut)
def update_approval(approval_id: int, payload: ApprovalUpdate, db: Session = Depends(get_db)) -> ApprovalOut:
    try:
        approval = ApprovalEngine(db).update_approval(approval_id, payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return approval


@router.post("/{approval_id}/review", response_model=ApprovalOut)
def start_review(approval_id: int, payload: ApprovalReviewRequest, db: Session = Depends(get_db)) -> ApprovalOut:
    try:
        approval = ApprovalEngine(db).start_review(
            approval_id,
            reviewer=payload.reviewer,
            assigned_to=payload.assigned_to,
            justification=payload.justification_human,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
def approve_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)) -> ApprovalOut:
    try:
        approval = ApprovalEngine(db).approve(approval_id, actor=payload.actor, justification=payload.justification_human, decision=payload.decision)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
def reject_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)) -> ApprovalOut:
    try:
        approval = ApprovalEngine(db).reject(approval_id, actor=payload.actor, justification=payload.justification_human)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return approval


@router.post("/{approval_id}/escalate", response_model=ApprovalOut)
def escalate_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)) -> ApprovalOut:
    try:
        approval = ApprovalEngine(db).transition(approval_id, "ESCALATED", actor=payload.actor, justification=payload.justification_human)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return approval


@router.post("/{approval_id}/cancel", response_model=ApprovalOut)
def cancel_approval(approval_id: int, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)) -> ApprovalOut:
    try:
        approval = ApprovalEngine(db).transition(approval_id, "CANCELLED", actor=payload.actor, justification=payload.justification_human)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return approval


@router.get("/{approval_id}/history")
def get_approval_history(approval_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    approval = ApprovalRepository(db).get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval introuvable.")
    return {"approval_id": approval_id, "events": approval_history(db, approval)}
