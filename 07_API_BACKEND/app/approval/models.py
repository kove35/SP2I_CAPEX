from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Approval(Base):
    """Decision enterprise traçable pour arbitrages CAPEX, achats et chantier."""

    __tablename__ = "fact_approvals"

    approval_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    simulation_id: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    procurement_action_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    article_id: Mapped[str] = mapped_column(String(150), nullable=False, default="", index=True)
    lot_id: Mapped[str] = mapped_column(String(150), nullable=False, default="", index=True)
    sous_lot_id: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    niveau_id: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    appartement_id: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    piece_id: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    ifc_guid: Mapped[str] = mapped_column(String(150), nullable=False, default="", index=True)

    approval_type: Mapped[str] = mapped_column(String(80), nullable=False, default="PROCUREMENT_ARBITRATION")
    decision: Mapped[str] = mapped_column(String(80), nullable=False, default="A_ARBITRER")
    status: Mapped[str] = mapped_column(String(80), nullable=False, default="PENDING", index=True)
    priority: Mapped[str] = mapped_column(String(40), nullable=False, default="MEDIUM")
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False, default="MEDIUM")
    roi: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_saving: Mapped[float | None] = mapped_column(Float, nullable=True)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    justification_ai: Mapped[str] = mapped_column(Text, nullable=False, default="")
    justification_human: Mapped[str] = mapped_column(Text, nullable=False, default="")

    requested_by: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    assigned_to: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    approved_by: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    rejected_by: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role_required: Mapped[str] = mapped_column(String(120), nullable=False, default="PROCUREMENT_MANAGER")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_fact_approvals_project_status", "project_id", "status"),
        Index("ix_fact_approvals_project_type", "project_id", "approval_type"),
        Index("ix_fact_approvals_project_deadline", "project_id", "deadline"),
        Index("ix_fact_approvals_governance_queue", "project_id", "role_required", "status", "priority"),
    )
