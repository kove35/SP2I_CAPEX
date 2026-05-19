from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyticsFilters(BaseModel):
    projet: str | None = None
    scenario: str | None = None
    batiment: str | None = None
    niveau: str | None = None
    lot: str | None = None
    famille: str | None = None
    fournisseur: str | None = None
    devise: str | None = None
    decision_import: str | None = None
    periode_debut: str | None = None
    periode_fin: str | None = None
    criticite: str | None = None
    statut_chantier: str | None = None


class AnalyticsQuery(BaseModel):
    filters: AnalyticsFilters = Field(default_factory=AnalyticsFilters)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=5000)
    group_by: str | None = None
    order_by: str | None = None
    order_dir: Literal["asc", "desc"] = "desc"
    aggregations: list[str] = Field(default_factory=list)
    drilldown_level: str | None = None


class AnalyticsResponse(BaseModel):
    status: str = "SUCCESS"
    filters: dict[str, Any] = Field(default_factory=dict)
    pagination: dict[str, Any] = Field(default_factory=dict)
    kpis: dict[str, Any] = Field(default_factory=dict)
    charts: dict[str, Any] = Field(default_factory=dict)
    table: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
