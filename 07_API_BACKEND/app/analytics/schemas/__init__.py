from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyticsFilters(BaseModel):
    projet: str | None = None
    scenario: str | None = None
    batiment: str | None = None
    niveau: str | None = None
    appartement: str | None = None
    zone: str | None = None
    piece: str | None = None
    sous_lot: str | None = None
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


class ProjectCostSummary(BaseModel):
    capex_direct: float = 0
    indirect_costs: float = 0
    site_installation: float = 0
    import_logistics: float = 0
    contingency: float = 0
    total_project_cost: float = 0
    capex_m2: float = 0
    cost_per_apartment: float = 0
    cost_per_level: float = 0


class DashboardDirectionV6(BaseModel):
    lot: str
    capex_direct: float = 0
    pct_capex_direct: float = 0
    nb_lignes: int = 0
    nb_articles: int = 0
    total_project_cost: float = 0
    capex_m2: float = 0


class CostIntelligenceV6(BaseModel):
    lot: str
    sous_lot: str | None = None
    article_code: str | None = None
    designation: str | None = None
    unite: str | None = None
    quantite: float = 0
    prix_local_fcfa: float = 0
    prix_import_fcfa: float = 0
    prix_optimise_fcfa: float = 0
    capex_local: float = 0
    capex_import: float = 0
    capex_optimise: float = 0
    economie: float = 0
    decision_import: str | None = None
    pricing_scope: str | None = None
    pricing_confidence: str | None = None
    price_reference_code: str | None = None
