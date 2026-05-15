from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_service_ai_mapping
from app.database import get_db
from app.schemas import ExcelUploadResponse
from app.services.service_ai_mapping import ServiceAIMapping
from app.services.service_pipeline import ServicePipeline
from sqlalchemy.orm import Session


router = APIRouter()


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

    if not fichier.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Le fichier doit etre un Excel .xlsx ou .xlsm.")

    contenu = await fichier.read()
    if not contenu:
        raise HTTPException(status_code=400, detail="Le fichier Excel est vide.")

    try:
        return service.analyser_excel(contenu, fichier.filename)
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

    if not fichier.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Le fichier doit etre un Excel .xlsx ou .xlsm.")

    contenu = await fichier.read()
    if not contenu:
        raise HTTPException(status_code=400, detail="Le fichier Excel est vide.")

    try:
        return ServicePipeline(db).executer_depuis_excel(contenu, fichier.filename)
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la synchronisation Excel : {erreur}",
        ) from erreur
