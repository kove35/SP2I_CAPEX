from __future__ import annotations

# ==========================================================
# 📦 IMPORTS
# ==========================================================
from fastapi import APIRouter, File, HTTPException, UploadFile
from typing import Dict

# 🔧 Service métier (orchestration pipeline SP2I)
from app.services.service_dqe import ServiceDQE


# ==========================================================
# 🚀 ROUTER FASTAPI
# ==========================================================
router = APIRouter(
    prefix="/dqe",              # 👉 URL : /dqe/upload
   
)


# ==========================================================
# 📤 ENDPOINT UPLOAD DQE
# ==========================================================
@router.post("/upload")
async def upload_dqe(fichier: UploadFile = File(...)) -> Dict:
    """
    📌 Upload d'un DQE au format JSON

    Ce endpoint :
    1. Vérifie le format du fichier
    2. Lit le contenu JSON
    3. Lance le pipeline SP2I complet :
        - Normalisation DQE
        - Enrichissement
        - Optimisation import/local
        - Génération dataset BI
        - Audit qualité
    4. Retourne un résumé + logs exploitables

    ----------------------------------------------------------
    📥 INPUT :
        fichier (UploadFile) → JSON DQE brut

    📤 OUTPUT :
        {
            "status": "SUCCESS" | "ERROR",
            "resume": {...},
            "logs": [...]
        }
    ----------------------------------------------------------
    """

    # ======================================================
    # 🛑 1. VALIDATION DU FICHIER
    # ======================================================
    if not fichier.filename:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier fourni."
        )

    if not fichier.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Le DQE doit être au format JSON (.json)."
        )

    # ======================================================
    # 📖 2. LECTURE DU FICHIER
    # ======================================================
    try:
        contenu = await fichier.read()

        if not contenu:
            raise HTTPException(
                status_code=400,
                detail="Le fichier est vide."
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture du fichier : {str(e)}"
        )

    # ======================================================
    # 🚀 3. TRAITEMENT VIA SERVICE MÉTIER
    # ======================================================
    try:
        service = ServiceDQE()

        # 🔥 Appel du pipeline complet SP2I
        resultat = service.traiter_upload_json(contenu)

        return resultat

    except Exception as e:
        # ==================================================
        # ❌ 4. GESTION ERREUR GLOBALE
        # ==================================================
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement SP2I : {str(e)}"
        )