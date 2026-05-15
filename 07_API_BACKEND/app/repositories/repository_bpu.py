from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class RepositoryBPU:
    """
    Acces aux sources DQE/BPU actuellement stockees en fichiers.

    Le service ne manipule plus directement les chemins : demain ce repository
    pourra lire PostgreSQL, parquet ou MongoDB sans changer le moteur metier.
    """

    def __init__(self, racine: Path) -> None:
        self.racine = racine
        self.chemin_dqe_normalise = racine / "03_DONNEES_ENTREE/dqe/dqe_normalise.json"
        self.chemin_optimisation = racine / "05_RESULTATS/optimisation_capex_import.csv"

    def lire_lignes_dqe(self) -> list[dict[str, Any]]:
        if not self.chemin_dqe_normalise.exists():
            return []

        donnees = json.loads(self.chemin_dqe_normalise.read_text(encoding="utf-8-sig"))
        if isinstance(donnees, dict):
            lignes = donnees.get("lignes", [])
        else:
            lignes = donnees
        return lignes if isinstance(lignes, list) else []

    def enregistrer_optimisation(self, lignes: list[dict[str, Any]]) -> None:
        self.chemin_optimisation.parent.mkdir(parents=True, exist_ok=True)
        if not lignes:
            self.chemin_optimisation.write_text("", encoding="utf-8")
            return

        champs = list(lignes[0].keys())
        with self.chemin_optimisation.open("w", encoding="utf-8-sig", newline="") as fichier:
            writer = csv.DictWriter(fichier, fieldnames=champs, delimiter=";")
            writer.writeheader()
            writer.writerows(lignes)
