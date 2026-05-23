from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(120), nullable=False, default="Pointe-Noire")
    country: Mapped[str] = mapped_column(String(120), nullable=False, default="Congo-Brazzaville")
    currency: Mapped[str] = mapped_column(String(12), nullable=False, default="FCFA")
    project_type: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    project_manager: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    target_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    vat_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="HT")
    reference_exchange_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_transport_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_customs_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_insurance_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_import_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_saving_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    site_storage_capacity: Mapped[float | None] = mapped_column(Float, nullable=True)
    setup_status: Mapped[str] = mapped_column(String(40), nullable=False, default="CONFIG_REQUIRED")
    setup_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_projects_owner", "owner_id"),
        Index("ix_projects_status", "status"),
    )
