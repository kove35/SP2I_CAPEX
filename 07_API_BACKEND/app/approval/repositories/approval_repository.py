from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.approval.models import Approval


class ApprovalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, values: dict[str, Any]) -> Approval:
        approval = Approval(**values)
        self.db.add(approval)
        self.db.flush()
        return approval

    def get(self, approval_id: int) -> Approval | None:
        return self.db.get(Approval, approval_id)

    def list(
        self,
        project_id: int | None = None,
        status: str | None = None,
        role_required: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Approval]:
        statement = select(Approval)
        if project_id is not None:
            statement = statement.where(Approval.project_id == project_id)
        if status:
            statement = statement.where(Approval.status == status)
        if role_required:
            statement = statement.where(Approval.role_required == role_required)
        statement = statement.order_by(Approval.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(statement).all())

    def summary(self, project_id: int) -> dict[str, Any]:
        rows = self.db.execute(
            select(Approval.status, func.count(Approval.approval_id))
            .where(Approval.project_id == project_id)
            .group_by(Approval.status)
        ).all()
        role_rows = self.db.execute(
            select(Approval.role_required, func.count(Approval.approval_id))
            .where(Approval.project_id == project_id)
            .group_by(Approval.role_required)
        ).all()
        saving_total = self.db.scalar(
            select(func.coalesce(func.sum(Approval.estimated_saving), 0)).where(Approval.project_id == project_id)
        )
        critical_count = self.db.scalar(
            select(func.count(Approval.approval_id)).where(
                Approval.project_id == project_id,
                Approval.risk_level.in_(["HIGH", "CRITICAL"]),
                Approval.status.not_in(["APPROVED", "REJECTED", "CANCELLED", "EXPIRED"]),
            )
        )
        by_status = {str(status): int(count) for status, count in rows}
        return {
            "project_id": project_id,
            "total_count": sum(by_status.values()),
            "pending_count": by_status.get("PENDING", 0),
            "under_review_count": by_status.get("UNDER_REVIEW", 0),
            "approved_count": by_status.get("APPROVED", 0),
            "rejected_count": by_status.get("REJECTED", 0),
            "escalated_count": by_status.get("ESCALATED", 0),
            "expired_count": by_status.get("EXPIRED", 0),
            "critical_count": int(critical_count or 0),
            "estimated_saving_total": float(saving_total or 0),
            "by_status": by_status,
            "by_role": {str(role): int(count) for role, count in role_rows},
        }
