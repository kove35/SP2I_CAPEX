from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FactMetre(Base):
    """Table de faits Power BI : une ligne = une ligne DQE exploitable."""

    __tablename__ = "fact_metre"

    id_ligne: Mapped[str] = mapped_column(String(100), primary_key=True)
    designation: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    quantite: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    prix_total_ht: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    capex_optimise: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    economie_nette: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    decision_import: Mapped[str] = mapped_column(String(50), nullable=False, default="LOCAL")
    lot: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    famille: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    batiment: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    niveau: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    statut_ligne: Mapped[str] = mapped_column(String(150), nullable=False, default="OK")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_fact_metre_famille", "famille"),
        Index("ix_fact_metre_lot", "lot"),
        Index("ix_fact_metre_batiment", "batiment"),
    )


class DimFamille(Base):
    """Dimension Power BI : une ligne = une famille travaux."""

    __tablename__ = "dim_famille"

    famille: Mapped[str] = mapped_column(String(100), primary_key=True)
    libelle_famille: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    categorie_achat: Mapped[str] = mapped_column(String(100), nullable=False, default="A_ANALYSER")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class MonitoringLog(Base):
    """
    Journal de monitoring.

    Cette table stocke les evenements et metriques techniques :
    temps de reponse API, etat base, score qualite, anomalies, erreurs.
    """

    __tablename__ = "monitoring_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False, default="event")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    niveau: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    valeur: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_monitoring_logs_type", "type"),
        Index("ix_monitoring_logs_niveau", "niveau"),
        Index("ix_monitoring_logs_created_at", "created_at"),
    )


class ProcurementDecision(Base):
    """
    Decision achat metier issue d'une recommandation IA puis validable par un humain.

    Cette table ne remplace pas `fact_simulation` : elle ajoute la couche
    enterprise de validation achat et conserve le lien vers la ligne simulee.
    """

    __tablename__ = "procurement_decisions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    scenario_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    simulation_line_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    lot: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    family: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    designation: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    ai_decision: Mapped[str] = mapped_column(String(50), nullable=False, default="REVIEW_REQUIRED")
    ai_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    ai_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    proposed_decision: Mapped[str] = mapped_column(String(50), nullable=False, default="REVIEW_REQUIRED")
    validated_decision: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    supplier_selected: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    supplier_country: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    purchase_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    estimated_local_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    estimated_import_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    estimated_savings: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, default="MEDIUM")
    validator_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    validator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "scenario_id", "simulation_line_id", name="uq_procurement_decision_source_line"),
        Index("ix_procurement_decisions_project_status", "project_id", "validation_status"),
    )


class SiteExecutionAction(Base):
    """
    Action chantier issue des arbitrages achat et des signaux logistiques.

    Cette table materialise le passage de l'approvisionnement valide vers un
    suivi operationnel chantier sans supprimer le fallback `fact_simulation`.
    """

    __tablename__ = "site_execution_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    scenario_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    procurement_decision_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    simulation_line_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    lot: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    family: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    designation: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, default="COORDINATION")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    problem: Mapped[str] = mapped_column(Text, nullable=False, default="")
    impact: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="MEDIUM")
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="TO_DO")
    responsible_role: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    responsible_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_eta_days: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    date_needed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delay_days: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    storage_impact: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    criticality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="procurement_decisions")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "scenario_id",
            "procurement_decision_id",
            "action_type",
            name="uq_site_execution_action_source",
        ),
        Index("ix_site_execution_actions_project_status", "project_id", "status"),
    )
