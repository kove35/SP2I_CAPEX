from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SimulationItem(BaseModel):
    """Une ligne DQE/BPU envoyee par React pour une simulation temps reel."""

    id_ligne: str | None = Field(default=None, description="Identifiant stable de la ligne DQE.")
    designation: str = Field(..., min_length=1, description="Designation travaux.")
    quantite: float = Field(default=1, gt=0, description="Quantite a simuler.")
    prix_total_ht: float = Field(default=0, ge=0, description="Montant local HT.")
    prix_unitaire_ht: float | None = Field(default=None, ge=0)
    famille: str | None = Field(default=None, description="Famille metier si connue.")
    lot: str | None = None
    batiment: str | None = None
    niveau: str | None = None
    unite: str | None = None
    prix_fob: float | None = Field(default=None, ge=0, description="Prix FOB unitaire si connu.")
    supplier_moq: float | None = Field(default=None, ge=0, description="MOQ fournisseur si connu.")
    project_criticality: str | None = Field(default=None, description="LOW, MEDIUM, HIGH ou CRITICAL.")
    cashflow_tension: str | None = Field(default=None, description="LOW, MEDIUM, HIGH ou CRITICAL.")
    reliability_score: float | None = Field(default=None, ge=0, le=100)
    quality_score: float | None = Field(default=None, ge=0, le=100)
    customs_risk: float | None = Field(default=None, ge=0, le=100)
    port_risk: float | None = Field(default=None, ge=0, le=100)
    logistics_risk: float | None = Field(default=None, ge=0, le=100)
    currency_risk: float | None = Field(default=None, ge=0, le=100)
    political_risk: float | None = Field(default=None, ge=0, le=100)
    supplier_production_days: float | None = Field(default=None, ge=0)
    sea_freight_days: float | None = Field(default=None, ge=0)
    customs_days: float | None = Field(default=None, ge=0)
    local_transport_days: float | None = Field(default=None, ge=0)
    security_buffer_days: float | None = Field(default=None, ge=0)
    volume_unitaire_m3: float | None = Field(default=None, ge=0)
    poids_unitaire_kg: float | None = Field(default=None, ge=0)
    supplier_city: str | None = None
    departure_port: str | None = None
    arrival_port: str | None = None
    supplier_availability_days: float | None = Field(default=None, ge=0)
    shipment_status: str | None = None
    required_on_site_days: float | None = Field(default=None, ge=0)
    site_storage_capacity_m3: float | None = Field(default=None, ge=0)
    storage_days: float | None = Field(default=None, ge=0)


class SimulationParameters(BaseModel):
    """Parametres modifiables par le frontend pour tester les hypotheses."""

    taux_landed_cost: dict[str, float] | None = Field(
        default=None,
        description="Taux transport, assurance, douane, port, logistique.",
    )
    seuil_decision_import: float = Field(default=0.97, gt=0, le=1.5)
    coefficient_risque: float = Field(default=1.10, gt=0, le=3)


class SimulationMetadata(BaseModel):
    """Informations techniques pour tracer une simulation."""

    simulation_id: str
    run_id: str
    scenario_id: str
    mode: Literal["strict", "tolerant"]
    lignes_entree: int
    lignes_calculees: int
    temps_calcul_secondes: float
    persist: bool = False


class SimulationWarning(BaseModel):
    """Avertissement metier non bloquant, surtout en mode tolerant."""

    index: int | None = None
    code: str
    message: str
    ligne: dict[str, Any] = Field(default_factory=dict)


class SimulationErrorResponse(BaseModel):
    """Erreur metier structuree retournee par l'API."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SimulationRequest(BaseModel):
    """Contrat d'entree pour lancer une simulation CAPEX."""

    items: list[SimulationItem] = Field(default_factory=list)
    parameters: SimulationParameters = Field(default_factory=SimulationParameters)
    inclure_sensibilite: bool = Field(default=False)
    mode: Literal["strict", "tolerant"] = Field(default="strict")
    summary_only: bool = Field(default=False)
    return_lines: bool = Field(default=True)
    persist: bool = Field(default=False)
    scenario_name: str | None = Field(default=None)
    scenario_type: str = Field(default="BASELINE")
    scenario_description: str = Field(default="")
    created_by: str = Field(default="system")


class SimulationLineResult(BaseModel):
    id_ligne: str | None = None
    designation: str
    famille: str
    lot: str | None = None
    quantite: float
    pu_local: float
    pu_import_ht: float
    capex_local: float
    capex_import: float
    capex_optimise: float
    economie_nette: float
    taux_import: float
    decision_import: Literal["IMPORT", "LOCAL"]
    score_confiance: float
    decision_finale: str | None = None
    decision_type: str | None = None
    decision_score: float | None = None
    decision_confidence: str | None = None
    decision_reason: dict[str, Any] = Field(default_factory=dict)
    global_risk_score: float | None = None
    risk_level: str | None = None
    lead_time_days: float | None = None
    cashflow_score: float | None = None
    moq_risk_score: float | None = None
    complexity_score: float | None = None
    procurement_analysis: dict[str, Any] = Field(default_factory=dict)
    container_strategy: str | None = None
    shipment_strategy: str | None = None
    fill_rate: float | None = None
    shipment_cost: float | None = None
    lead_time_total: float | None = None
    storage_cost: float | None = None
    delivery_risk: str | None = None
    logistics_analysis: dict[str, Any] = Field(default_factory=dict)


class SimulationKPI(BaseModel):
    lignes: int
    capex_local: float
    capex_import: float
    capex_optimise: float
    economie_nette: float
    taux_economie: float
    lignes_import: int
    lignes_local: int


class SimulationResponse(BaseModel):
    status: Literal["SUCCESS", "EMPTY", "ERROR"]
    kpi: SimulationKPI
    lignes: list[SimulationLineResult]
    sensibilite: list[dict[str, Any]] = Field(default_factory=list)
    metadata: SimulationMetadata | None = None
    warnings: list[SimulationWarning] = Field(default_factory=list)
    errors: list[SimulationErrorResponse] = Field(default_factory=list)


class ScenarioRequest(BaseModel):
    """Contrat dedie aux analyses de sensibilite multi-scenarios."""

    items: list[SimulationItem] = Field(default_factory=list)
    parameters: SimulationParameters = Field(default_factory=SimulationParameters)
    variations_landed_cost: list[float] = Field(default_factory=lambda: [-0.1, 0, 0.1])
    mode: Literal["strict", "tolerant"] = Field(default="strict")


class FactMetreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_ligne: str
    designation: str
    quantite: float
    prix_total_ht: float
    capex_optimise: float
    economie_nette: float
    decision_import: str
    lot: str
    famille: str
    batiment: str
    niveau: str
    statut_ligne: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DimFamilleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    famille: str
    libelle_famille: str
    categorie_achat: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CapexSummary(BaseModel):
    capex_local: float
    capex_optimise: float
    economie: float
    lignes: int
