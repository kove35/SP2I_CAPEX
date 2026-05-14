from __future__ import annotations

import json
from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.service_dqe import ServiceDQE
from app.services.service_pipeline import ServicePipeline


router = APIRouter()


@router.post("/upload")
async def upload_dqe(fichier: UploadFile = File(...), db: Session = Depends(get_db)) -> Dict:
    """
    Upload d'un DQE au format JSON.

    Ce endpoint verifie le fichier, lit son contenu, lance le pipeline
    complet SP2I, puis retourne un resultat compatible API.
    """
    if not fichier.filename:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier fourni.",
        )

    if not fichier.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Le DQE doit etre au format JSON (.json).",
        )

    try:
        contenu = await fichier.read()

        if not contenu:
            raise HTTPException(
                status_code=400,
                detail="Le fichier est vide.",
            )
    except HTTPException:
        raise
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture du fichier : {str(erreur)}",
        )

    try:
        return ServiceDQE(db).traiter_upload_json(contenu)
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement SP2I : {str(erreur)}",
        )


@router.post("/sync-current")
def sync_current_dqe(db: Session = Depends(get_db)) -> Dict:
    """Relance le pipeline sur le DQE source courant et synchronise PostgreSQL."""
    try:
        return ServicePipeline(db).executer_source_courante()
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la synchronisation PostgreSQL : {str(erreur)}",
        )


@router.post("/extract")
async def extract_dqe_pdf(
    fichier: UploadFile | None = File(default=None),
    file: UploadFile | None = File(default=None),
) -> Dict:
    """
    Upload d'un DQE PDF pour extraire un apercu texte.

    Le endpoint accepte les champs `fichier` et `file` pour rester compatible
    avec Swagger, curl et les interfaces React de test.
    """
    fichier_recu = fichier or file

    if not fichier_recu or not fichier_recu.filename:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier PDF fourni.",
        )

    if not fichier_recu.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit etre au format PDF (.pdf).",
        )

    try:
        contenu = await fichier_recu.read()

        if not contenu:
            raise HTTPException(
                status_code=400,
                detail="Le fichier PDF est vide.",
            )
    except HTTPException:
        raise
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture du PDF : {str(erreur)}",
        )

    try:
        return ServiceDQE().extraire_pdf(contenu, fichier_recu.filename)
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'extraction PDF : {str(erreur)}",
        )


@router.get("/stats")
def stats_dqe() -> Dict:
    """Retourne quelques statistiques simples sur le dernier DQE normalise."""
    service = ServiceDQE()
    chemin_normalise = service.chemin_source.parent / "dqe_normalise.json"

    if not chemin_normalise.exists():
        raise HTTPException(
            status_code=404,
            detail="Aucun DQE normalise disponible. Lance d'abord le pipeline.",
        )

    try:
        donnees = json.loads(chemin_normalise.read_text(encoding="utf-8"))
        lignes = donnees.get("lignes", []) if isinstance(donnees, dict) else []
    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture des statistiques : {str(erreur)}",
        )

    return {
        "status": "SUCCESS",
        "nombre_lignes": len(lignes),
        "lignes_ok": sum(1 for ligne in lignes if ligne.get("statut_ligne") == "OK"),
        "lignes_anomalie": sum(1 for ligne in lignes if ligne.get("statut_ligne") != "OK"),
    }
