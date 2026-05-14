from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
