from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.approval.models import Approval
from app.approval.repositories.approval_repository import ApprovalRepository
from app.approval.services.approval_history import log_approval_history
from app.approval.services.approval_notifications import ApprovalNotificationService
from app.approval.services.approval_rules import (
    APPROVAL_TYPES,
    PRIORITIES,
    RISK_LEVELS,
    default_deadline,
    initial_status_for_role,
    normalize_choice,
    normalize_decision,
    resolve_required_role,
)
from app.approval.services.approval_workflow import assert_transition_allowed, normalize_status


class ApprovalEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ApprovalRepository(db)
        self.notifications = ApprovalNotificationService()

    def create_approval(self, values: dict[str, Any], user_id: int | None = None) -> Approval:
        payload = self._normalize_create(values)
        approval = self.repository.create(payload)
        log_approval_history(
            self.db,
            approval,
            "APPROVAL_CREATED",
            message="Demande d'approbation enterprise creee.",
            user_id=user_id,
            metadata=self.notifications.build_notification("APPROVAL_CREATED", approval),
        )
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def update_approval(self, approval_id: int, values: dict[str, Any], user_id: int | None = None) -> Approval | None:
        approval = self.repository.get(approval_id)
        if not approval:
            return None
        previous_status = approval.status
        payload = {key: value for key, value in values.items() if value is not None}
        if "status" in payload:
            payload["status"] = normalize_status(payload["status"])
            assert_transition_allowed(approval.status, payload["status"])
        if "decision" in payload:
            payload["decision"] = normalize_decision(payload["decision"])
        if "priority" in payload:
            payload["priority"] = normalize_choice(payload["priority"], PRIORITIES, approval.priority)
        if "risk_level" in payload:
            payload["risk_level"] = normalize_choice(payload["risk_level"], RISK_LEVELS, approval.risk_level)

        for key, value in payload.items():
            setattr(approval, key, value)
        log_approval_history(
            self.db,
            approval,
            "APPROVAL_UPDATED",
            previous_status=previous_status,
            message="Demande d'approbation mise a jour.",
            user_id=user_id,
            metadata=payload,
        )
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def start_review(self, approval_id: int, reviewer: str = "", assigned_to: str | None = None, justification: str = "", user_id: int | None = None) -> Approval | None:
        approval = self.repository.get(approval_id)
        if not approval:
            return None
        previous_status = approval.status
        assert_transition_allowed(previous_status, "UNDER_REVIEW")
        approval.status = "UNDER_REVIEW"
        approval.assigned_to = assigned_to if assigned_to is not None else approval.assigned_to
        approval.justification_human = justification or approval.justification_human
        log_approval_history(
            self.db,
            approval,
            "APPROVAL_REVIEW_STARTED",
            previous_status=previous_status,
            message=f"Revue demarree par {reviewer or 'workflow'}.".strip(),
            user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def approve(self, approval_id: int, actor: str = "", justification: str = "", decision: str | None = None, user_id: int | None = None) -> Approval | None:
        approval = self.repository.get(approval_id)
        if not approval:
            return None
        previous_status = approval.status
        assert_transition_allowed(previous_status, "APPROVED")
        approval.status = "APPROVED"
        approval.decision = normalize_decision(decision or approval.decision)
        if approval.decision == "A_ARBITRER":
            approval.decision = "APPROVED"
        approval.approved_by = actor
        approval.approved_at = datetime.now(timezone.utc)
        approval.justification_human = justification or approval.justification_human
        log_approval_history(self.db, approval, "APPROVAL_APPROVED", previous_status, "Decision approuvee.", user_id)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def reject(self, approval_id: int, actor: str = "", justification: str = "", user_id: int | None = None) -> Approval | None:
        approval = self.repository.get(approval_id)
        if not approval:
            return None
        previous_status = approval.status
        assert_transition_allowed(previous_status, "REJECTED")
        approval.status = "REJECTED"
        approval.decision = "REJECTED"
        approval.rejected_by = actor
        approval.rejected_at = datetime.now(timezone.utc)
        approval.justification_human = justification or approval.justification_human
        log_approval_history(self.db, approval, "APPROVAL_REJECTED", previous_status, "Decision rejetee.", user_id)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def transition(self, approval_id: int, next_status: str, actor: str = "", justification: str = "", user_id: int | None = None) -> Approval | None:
        approval = self.repository.get(approval_id)
        if not approval:
            return None
        status = normalize_status(next_status)
        previous_status = approval.status
        assert_transition_allowed(previous_status, status)
        approval.status = status
        approval.justification_human = justification or approval.justification_human
        if status == "EXPIRED":
            approval.rejected_at = datetime.now(timezone.utc)
        log_approval_history(
            self.db,
            approval,
            f"APPROVAL_{status}",
            previous_status=previous_status,
            message=f"Transition executee par {actor or 'workflow'} vers {status}.",
            user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def _normalize_create(self, values: dict[str, Any]) -> dict[str, Any]:
        payload = dict(values)
        payload["approval_type"] = normalize_choice(payload.get("approval_type"), APPROVAL_TYPES, "PROCUREMENT_ARBITRATION")
        payload["decision"] = normalize_decision(payload.get("decision"))
        payload["priority"] = normalize_choice(payload.get("priority"), PRIORITIES, "MEDIUM")
        payload["risk_level"] = normalize_choice(payload.get("risk_level"), RISK_LEVELS, "MEDIUM")
        payload["role_required"] = payload.get("role_required") or resolve_required_role(payload)
        payload["status"] = normalize_status(payload.get("status") or initial_status_for_role(payload["role_required"]))
        payload["deadline"] = payload.get("deadline") or default_deadline(payload["priority"], payload["risk_level"])
        return payload
