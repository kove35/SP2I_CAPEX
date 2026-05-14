from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

RACINE = Path(__file__).resolve().parents[3]
TRAITEMENT = RACINE / "04_TRAITEMENT"

if str(TRAITEMENT) not in sys.path:
    sys.path.insert(0, str(TRAITEMENT))

from pipeline_complet import PipelineCompletSP2I  # noqa: E402
from app.services.service_pipeline import ServicePipeline


class ServiceDQE:
    """Service metier utilise par l'API pour traiter un DQE JSON."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.chemin_source = RACINE / "03_DONNEES_ENTREE/dqe/dqe_source_brut.json"

    def traiter_upload_json(self, contenu: bytes) -> dict:
        """Sauvegarde le JSON envoye, lance le pipeline, puis retourne le resultat."""
        return ServicePipeline(self.db).executer_depuis_json(contenu)

    def extraire_pdf(self, contenu: bytes, nom_fichier: str) -> dict[str, Any]:
        """Extrait un aperçu texte d'un PDF pour tester l'API depuis le frontend."""
        debut = perf_counter()

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("La dependance pypdf est requise pour extraire un PDF.") from exc

        with NamedTemporaryFile(suffix=".pdf", delete=False) as fichier_temporaire:
            fichier_temporaire.write(contenu)
            chemin_pdf = Path(fichier_temporaire.name)

        try:
            reader = PdfReader(str(chemin_pdf))
            lignes: list[dict[str, Any]] = []

            for numero_page, page in enumerate(reader.pages, start=1):
                texte_page = page.extract_text() or ""

                for numero_ligne, texte in enumerate(texte_page.splitlines(), start=1):
                    texte = texte.strip()
                    if not texte:
                        continue

                    lignes.append(
                        {
                            "page": numero_page,
                            "ligne": numero_ligne,
                            "texte": texte,
                        }
                    )

            duree = round(perf_counter() - debut, 2)

            return {
                "status": "SUCCESS",
                "fichier": nom_fichier,
                "nombre_pages": len(reader.pages),
                "nombre_lignes": len(lignes),
                "temps_traitement": duree,
                "lignes": lignes[:50],
                "logs": [
                    "STEP 1 - Reception PDF",
                    "STEP 2 - Extraction texte PDF",
                    "STEP 3 - Generation preview",
                ],
            }
        finally:
            chemin_pdf.unlink(missing_ok=True)
