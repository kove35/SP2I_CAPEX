from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.services.service_db import ServiceDB


RACINE = Path(__file__).resolve().parents[3]
TRAITEMENT = RACINE / "04_TRAITEMENT"

if str(TRAITEMENT) not in sys.path:
    sys.path.insert(0, str(TRAITEMENT))

from pipeline_complet import PipelineCompletSP2I  # noqa: E402


def _lire_csv(chemin: Path) -> list[dict[str, Any]]:
    if not chemin.exists():
        return []

    with chemin.open("r", encoding="utf-8-sig", newline="") as fichier:
        return list(csv.DictReader(fichier, delimiter=";"))


class ServicePipeline:
    """Orchestre le pipeline existant puis synchronise PostgreSQL."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.chemin_source = RACINE / "03_DONNEES_ENTREE/dqe/dqe_source_brut.json"
        self.chemin_fact = RACINE / "06_ANALYSE_BI/dataset/FACT_METRE.csv"
        self.chemin_dim_famille = RACINE / "06_ANALYSE_BI/dataset/DIM_FAMILLE.csv"

    def executer_depuis_json(self, contenu: bytes) -> dict[str, Any]:
        try:
            donnees = json.loads(contenu.decode("utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ValueError("JSON DQE invalide") from exc

        self.chemin_source.parent.mkdir(parents=True, exist_ok=True)
        with self.chemin_source.open("w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, ensure_ascii=False, indent=2)

        return self.executer_source_courante()

    def executer_source_courante(self) -> dict[str, Any]:
        resultat = PipelineCompletSP2I(RACINE).executer()

        if resultat.get("status") != "SUCCESS":
            return resultat

        db_sync = self.synchroniser_exports_bi()
        resultat["db_sync"] = db_sync
        resultat.setdefault("logs", []).extend(db_sync.get("logs", []))
        return resultat

    def synchroniser_exports_bi(self) -> dict[str, Any]:
        logs: list[str] = []

        if self.db is None:
            return {
                "status": "SKIPPED",
                "fact_metre": 0,
                "dim_famille": 0,
                "logs": ["DB sync ignored: aucune session DB fournie."],
            }

        try:
            fact_metre = _lire_csv(self.chemin_fact)
            dim_famille = _lire_csv(self.chemin_dim_famille)
            service_db = ServiceDB(self.db)
            familles = service_db.insert_dim_famille(dim_famille)
            faits = service_db.insert_fact_metre(fact_metre)
            logs.append(f"DB sync OK: {faits} lignes FACT_METRE.")
            logs.append(f"DB sync OK: {familles} lignes DIM_FAMILLE.")

            return {
                "status": "SUCCESS",
                "fact_metre": faits,
                "dim_famille": familles,
                "logs": logs,
            }
        except Exception as erreur:
            self.db.rollback()
            return {
                "status": "ERROR",
                "fact_metre": 0,
                "dim_famille": 0,
                "error": str(erreur),
                "logs": [f"DB sync ERROR: {erreur}"],
            }
