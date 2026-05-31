from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_service_ai_mapping
from app.core.ai.ai_file_store import AIFileStore
from app.database import get_db
from app.schemas import ExcelUploadResponse
from app.services.service_ai_mapping import ServiceAIMapping
from app.services.service_pipeline import ServicePipeline
from app.utils.json_safe import sanitize_for_json
from sqlalchemy.orm import Session


router = APIRouter()

SUPPORTED_TABLE_FILES = (".xlsx", ".xlsm", ".xls", ".csv")


def _max_upload_bytes() -> int:
    """Retourne la taille maximale autorisee pour les uploads cloud."""
    try:
        max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "25"))
    except ValueError:
        max_upload_mb = 25
    return max_upload_mb * 1024 * 1024


def _valider_fichier_tabulaire(nom_fichier: str, contenu: bytes) -> None:
    if not nom_fichier.lower().endswith(SUPPORTED_TABLE_FILES):
        formats = ", ".join(SUPPORTED_TABLE_FILES)
        raise HTTPException(
            status_code=400,
            detail=f"Le fichier doit etre au format {formats}.",
        )

    if not contenu:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")

    if len(contenu) > _max_upload_bytes():
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux. Taille maximale: {os.getenv('MAX_UPLOAD_MB', '25')} Mo.",
        )


@router.post("/excel", response_model=ExcelUploadResponse)
async def upload_excel_intelligent(
    fichier: UploadFile = File(...),
    service: ServiceAIMapping = Depends(get_service_ai_mapping),
) -> dict:
    """
    Analyse un Excel DQE/BPU et retourne une preview normalisee.

    Cet endpoint est volontairement non destructif : il ne remplace pas encore
    le DQE courant et ne synchronise pas PostgreSQL. Il prepare le futur drag &
    drop React tout en preservant les routes existantes.
    """
    if not fichier.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    contenu = await fichier.read()
    _valider_fichier_tabulaire(fichier.filename, contenu)

    try:
        resultat = service.analyser_excel(contenu, fichier.filename)
        resultat["file_id"] = AIFileStore.save(resultat)
        print("RAW EXCEL ROWS:", sum(int(item.get("lignes_detectees") or 0) for item in resultat.get("analyses", [])))
        print("PARSER ROWS:", resultat.get("parser_rows_count", 0))
        print("GOVERNANCE ROWS:", resultat.get("governance_rows_count", 0))
        print("CLEANER ROWS:", resultat.get("normalized_lines_count", 0))
        print("FACT_METRE ROWS:", 0)
        print("PREVIEW ROWS:", resultat.get("preview_rows_count", 0))
        print("SYNCED ROWS:", 0)
        return sanitize_for_json(resultat)
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse Excel : {erreur}",
        ) from erreur


@router.post("/excel/sync")
async def upload_excel_et_synchroniser(
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Importe un Excel complet dans le pipeline analytique.

    Contrairement a `/api/upload/excel`, ce endpoint est destructif au sens
    metier : il remplace le DQE source courant, regenere les datasets et
    synchronise PostgreSQL. Il est separe pour eviter les mauvaises surprises
    lors des previews React.
    """
    if not fichier.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    contenu = await fichier.read()
    _valider_fichier_tabulaire(fichier.filename, contenu)

    try:
        resultat = ServicePipeline(db).executer_depuis_excel(contenu, fichier.filename)
        data_quality = ((resultat.get("db_sync") or {}).get("data_quality") or {})
        print("RAW EXCEL ROWS:", data_quality.get("lignes_excel", 0))
        print("PARSER ROWS:", data_quality.get("lignes_parsees", 0))
        print("GOVERNANCE ROWS:", (data_quality.get("governance_quality") or {}).get("total_rows", 0))
        print("CLEANER ROWS:", (resultat.get("resume") or {}).get("lignes_dqe", 0))
        print("FACT_METRE ROWS:", data_quality.get("lignes_fact_metre", 0))
        print("PREVIEW ROWS:", (resultat.get("audit_excel") or {}).get("preview_rows_count", 0))
        print("SYNCED ROWS:", (resultat.get("db_sync") or {}).get("fact_metre_sql_count", 0))
        return sanitize_for_json(resultat)
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la synchronisation Excel : {erreur}",
        ) from erreur
