from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
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
