from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExcelColumnMapping(BaseModel):
    colonne_excel: str
    champ_standard: str
    confiance: float = Field(ge=0, le=1)
    raison: str


class ExcelSheetAnalysis(BaseModel):
    feuille: str
    ligne_entete: int | None
    score_dqe: float = Field(ge=0, le=1)
    lignes_detectees: int
    mapping: list[ExcelColumnMapping]
    avertissements: list[str] = Field(default_factory=list)


class ExcelUploadResponse(BaseModel):
    status: str
    fichier: str
    feuille_recommandee: str | None
    analyses: list[ExcelSheetAnalysis]
    lignes_normalisees_preview: list[dict[str, Any]]
    simulation_preview: dict[str, Any] | None = None
    lineage: dict[str, Any] | None = None
