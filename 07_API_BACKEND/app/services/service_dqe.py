from __future__ import annotations

import json
import sys
from pathlib import Path

# ==========================================================
# 📂 PATH PROJET (important pour import pipeline)
# ==========================================================
RACINE = Path(__file__).resolve().parents[3]
TRAITEMENT = RACINE / "04_TRAITEMENT"

if str(TRAITEMENT) not in sys.path:
    sys.path.insert(0, str(TRAITEMENT))

# 🚀 IMPORT PIPELINE COMPLET
from pipeline_complet import PipelineCompletSP2I  # noqa


# ==========================================================
# 🚀 SERVICE DQE (VERSION SAAS)
# ==========================================================
class ServiceDQE:
    """
    Service métier SP2I

    👉 Gère :
    - Upload JSON DQE
    - Sauvegarde fichier source
    - Exécution pipeline complet
    - Retour résultat API
    """

    def __init__(self) -> None:
        self.chemin_source = RACINE / "03_DONNEES_ENTREE/dqe/dqe_source_brut.json"

    # ======================================================
    # 🚀 TRAITEMENT UPLOAD JSON
    # ======================================================
    def traiter_upload_json(self, contenu: bytes) -> dict:

        print("🔥 PIPELINE COMPLET SP2I LANCÉ")  # DEBUG VISUEL

        # ==================================================
        # 📖 1. LECTURE JSON
        # ==================================================
        try:
            donnees = json.loads(contenu.decode("utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ValueError("JSON DQE invalide") from exc

        # ==================================================
        # 💾 2. SAUVEGARDE FICHIER SOURCE
        # ==================================================
        self.chemin_source.parent.mkdir(parents=True, exist_ok=True)

        with open(self.chemin_source, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)

        # ==================================================
        # 🚀 3. EXECUTION PIPELINE COMPLET
        # ==================================================
        pipeline = PipelineCompletSP2I()
        resultat = pipeline.executer()

        # ==================================================
        # 📤 4. RETOUR API
        # ==================================================
        return resultat