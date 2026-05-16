from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExcelColumnMapping(BaseModel):
    colonne_excel: str
    colonne_index: int | None = None
    champ_standard: str
    confiance: float = Field(ge=0, le=1)
    raison: str
    strategy: str | None = None


class ExcelSheetAnalysis(BaseModel):
    feuille: str
    ligne_entete: int | None
    score_dqe: float = Field(ge=0, le=1)
    lignes_detectees: int
    mapping: list[ExcelColumnMapping]
    classification: dict[str, Any] | None = None
    ai_strategy: str | None = None
    avertissements: list[str] = Field(default_factory=list)


class ExcelUploadResponse(BaseModel):
    status: str
    file_id: str | None = None
    fichier: str
    feuille_recommandee: str | None
    analyses: list[ExcelSheetAnalysis]
    lignes_normalisees_preview: list[dict[str, Any]]
    simulation_preview: dict[str, Any] | None = None
    ai_preview: dict[str, Any] | None = None
    ai_confidence: dict[str, Any] | None = None
    ai_anomalies: list[dict[str, Any]] = Field(default_factory=list)
    ai_classified_rows: list[dict[str, Any]] = Field(default_factory=list)
    ai_suggestions: dict[str, Any] | None = None
    lineage: dict[str, Any] | None = None
