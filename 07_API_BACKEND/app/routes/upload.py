from __future__ import annotations

import os
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_service_ai_mapping
from app.auth.dependencies import require_analyst, require_manager
from app.core.ai.ai_file_store import AIFileStore
from app.database import get_db
from app.schemas import ExcelUploadResponse
from app.services.service_ai_mapping import ServiceAIMapping
from app.services.service_pipeline import ServicePipeline
from app.utils.json_safe import sanitize_for_json
from app.utils.upload_security import read_limited_upload, safe_upload_name, validate_file_signature
from sqlalchemy.orm import Session


router = APIRouter()
logger = logging.getLogger("sp2i-capex-api")

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


@router.post("/excel", response_model=ExcelUploadResponse, dependencies=[Depends(require_analyst)])
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
    nom_fichier = safe_upload_name(fichier.filename)
    contenu = await read_limited_upload(fichier, _max_upload_bytes())
    _valider_fichier_tabulaire(nom_fichier, contenu)
    validate_file_signature(nom_fichier, contenu)

    try:
        resultat = service.analyser_excel(contenu, nom_fichier)
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
        logger.exception("Excel analysis failed")
        raise HTTPException(
            status_code=500,
            detail="Erreur interne lors de l'analyse Excel.",
        ) from erreur


@router.post("/excel/sync", dependencies=[Depends(require_manager)])
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
    nom_fichier = safe_upload_name(fichier.filename)
    contenu = await read_limited_upload(fichier, _max_upload_bytes())
    _valider_fichier_tabulaire(nom_fichier, contenu)
    validate_file_signature(nom_fichier, contenu)

    try:
        resultat = ServicePipeline(db).executer_depuis_excel(contenu, nom_fichier)
        if resultat.get("status") != "SUCCESS" or (resultat.get("db_sync") or {}).get("status") == "ERROR":
            raise HTTPException(
                status_code=422,
                detail="Synchronisation bloquee par les controles de qualite; le dataset precedent a ete restaure.",
            )
        data_quality = ((resultat.get("db_sync") or {}).get("data_quality") or {})
        print("RAW EXCEL ROWS:", data_quality.get("lignes_excel", 0))
        print("PARSER ROWS:", data_quality.get("lignes_parsees", 0))
        print("GOVERNANCE ROWS:", (data_quality.get("governance_quality") or {}).get("total_rows", 0))
        print("CLEANER ROWS:", (resultat.get("resume") or {}).get("lignes_dqe", 0))
        print("FACT_METRE ROWS:", data_quality.get("lignes_fact_metre", 0))
        print("PREVIEW ROWS:", (resultat.get("audit_excel") or {}).get("preview_rows_count", 0))
        print("SYNCED ROWS:", (resultat.get("db_sync") or {}).get("fact_metre_sql_count", 0))
        return sanitize_for_json(resultat)
    except HTTPException:
        raise
    except Exception as erreur:
        db.rollback()
        logger.exception("Excel synchronization failed")
        raise HTTPException(
            status_code=500,
            detail="Erreur interne lors de la synchronisation Excel.",
        ) from erreur
