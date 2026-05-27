from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.approval.models import Approval
from app.services.workflow_events import list_workflow_events, log_workflow_event


def log_approval_history(
    db: Session,
    approval: Approval,
    event_type: str,
    previous_status: str = "",
    message: str = "",
    user_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    log_workflow_event(
        db,
        project_id=int(approval.project_id),
        event_type=event_type,
        entity_type="FACT_APPROVALS",
        entity_id=str(approval.approval_id),
        previous_status=previous_status,
        new_status=approval.status,
        message=message,
        user_id=user_id,
        metadata=metadata or {},
    )


def approval_history(db: Session, approval: Approval) -> list[dict[str, Any]]:
    events = list_workflow_events(db, project_id=int(approval.project_id), limit=500)
    return [event for event in events if str(event.get("entity_id")) == str(approval.approval_id)]
