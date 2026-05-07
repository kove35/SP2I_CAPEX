from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
TRAITEMENT = RACINE / "04_TRAITEMENT"
if str(TRAITEMENT) not in sys.path:
    sys.path.insert(0, str(TRAITEMENT))

from optimisation_import import OptimiseurImport  # noqa: E402
from utils.helpers import lire_json  # noqa: E402


class ServiceImport:
    def __init__(self) -> None:
        self.chemin_entree = RACINE / "03_DONNEES_ENTREE/dqe/dqe_normalise.json"
        self.chemin_sortie = RACINE / "05_RESULTATS/optimisation_capex_import.csv"
        self.chemin_parametres = RACINE / "01_PARAMETRES/parametres_import_pointe_noire.json"

    def optimiser_source_courante(self) -> dict:
        parametres = lire_json(self.chemin_parametres) if self.chemin_parametres.exists() else {}
        lignes = OptimiseurImport(parametres).optimiser_fichier(self.chemin_entree, self.chemin_sortie)
        montant_local = sum(ligne["MONTANT_LOCAL"] for ligne in lignes)
        capex_optimise = sum(ligne["CAPEX_OPTIMISE"] for ligne in lignes)
        return {
            "statut": "IMPORT_OPTIMISE",
            "lignes": len(lignes),
            "montant_local": round(montant_local, 2),
            "capex_optimise": round(capex_optimise, 2),
            "economie_nette": round(montant_local - capex_optimise, 2),
            "fichier_resultat": str(self.chemin_sortie),
        }
