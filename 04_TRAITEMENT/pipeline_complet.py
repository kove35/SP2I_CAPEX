from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from normalisation_dqe import NormalisateurDQE
from optimisation_import import OptimiseurImport
from utils.helpers import ecrire_csv, ecrire_json, lire_json, racine_projet


class PipelineCompletSP2I:
    """Orchestration metier: JSON DQE -> normalisation -> CAPEX -> datasets BI."""

    FAMILLES_TECHNIQUES_IMPORTABLES = {
        "alucobond",
        "ascenseur",
        "climatisation",
        "electricite",
        "menuiserie",
        "plomberie",
    }

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or racine_projet()
        self.chemins = {
            "source": self.base_dir / "03_DONNEES_ENTREE/dqe/dqe_source_brut.json",
            "normalise": self.base_dir / "03_DONNEES_ENTREE/dqe/dqe_normalise.json",
            "enrichi": self.base_dir / "03_DONNEES_ENTREE/dqe/dqe_enrichi.json",
            "parametres": self.base_dir / "01_PARAMETRES/parametres_import_pointe_noire.json",
            "dqe_powerbi": self.base_dir / "05_RESULTATS/dqe_pret_powerbi.csv",
            "optimisation": self.base_dir / "05_RESULTATS/optimisation_capex_import.csv",
            "audit": self.base_dir / "05_RESULTATS/audit_qualite_dqe.xlsx",
            "fact_metre": self.base_dir / "06_ANALYSE_BI/dataset/FACT_METRE.csv",
            "dim_famille": self.base_dir / "06_ANALYSE_BI/dataset/DIM_FAMILLE.csv"
        }

    def executer(self) -> dict[str, Any]:
        logs: list[str] = []

        try:
            logs.append("STEP 0 - Verification des fichiers et dossiers")
            self._verifier_fichiers()

            logs.append("STEP 1 - Normalisation DQE")
            normalisateur = NormalisateurDQE()
            lignes_dqe = normalisateur.normaliser_fichier(self.chemins["source"], self.chemins["normalise"])

            logs.append("STEP 2 - Enrichissement")
            ecrire_json(self.chemins["enrichi"], {"lignes": lignes_dqe})
            ecrire_csv(self.chemins["dqe_powerbi"], lignes_dqe)

            logs.append("STEP 3 - Optimisation import")
            parametres = lire_json(self.chemins["parametres"]) if self.chemins["parametres"].exists() else {}
            lignes_capex = OptimiseurImport(parametres).optimiser_lignes(lignes_dqe)
            ecrire_csv(self.chemins["optimisation"], lignes_capex)

            logs.append("STEP 4 - Generation dataset BI")
            self._generer_dataset_bi(lignes_dqe, lignes_capex)

            logs.append("STEP 5 - Audit qualite")
            self._generer_audit_qualite(lignes_dqe)

            return {
                "status": "SUCCESS",
                "resume": self._resume(lignes_dqe, lignes_capex),
                "logs": logs,
            }
        except Exception as erreur:
            logs.append(f"ERROR - {erreur}")
            return {
                "status": "ERROR",
                "error": str(erreur),
                "logs": logs,
            }

    def _verifier_fichiers(self) -> None:
        """Verifie les prerequis du pipeline avant de lancer les calculs."""
        if not self.chemins["source"].exists():
            raise FileNotFoundError(f"Fichier source introuvable: {self.chemins['source']}")

        # Les exports SaaS/BI doivent toujours avoir un dossier cible disponible.
        for nom in ("normalise", "enrichi", "dqe_powerbi", "optimisation", "audit", "fact_metre", "dim_famille"):
            self.chemins[nom].parent.mkdir(parents=True, exist_ok=True)

    def _generer_dataset_bi(self, lignes_dqe: list[dict[str, Any]], lignes_capex: list[dict[str, Any]]) -> None:
        capex_par_id = {
            ligne.get("id_ligne") or ligne.get("cle_metier"): ligne
            for ligne in lignes_capex
            if ligne.get("id_ligne") or ligne.get("cle_metier")
        }
        fact_metre: list[dict[str, Any]] = []
        familles: dict[str, dict[str, Any]] = {}

        for ligne in lignes_dqe:
            quantite = self._valeur_numerique(ligne.get("quantite"))
            prix_total_ht = self._valeur_numerique(ligne.get("prix_total_ht"))

            # Une ligne sans quantite ou sans prix ne doit pas polluer FACT_METRE.
            if quantite <= 0 or prix_total_ht <= 0:
                continue

            capex = capex_par_id.get(
                ligne.get("id_ligne") or ligne.get("cle_metier"),
                {},
            )
            famille = str(ligne.get("famille") or "default").lower().strip()
            familles.setdefault(
                famille,
                {
                    "famille": famille,
                    "libelle_famille": famille.replace("_", " ").title(),
                    "categorie_achat": self._categorie_achat(famille),
                },
            )
            fact_metre.append(
                {
                    "id_ligne": ligne.get("id_ligne", ""),
                    "cle_metier": ligne.get("cle_metier", ""),
                    "lot": ligne.get("lot", ""),
                    "famille": famille,
                    "batiment": ligne.get("batiment", ""),
                    "niveau": ligne.get("niveau", ""),
                    "designation": ligne.get("designation", ""),
                    "quantite": quantite,
                    "unite": ligne.get("unite", ""),
                    "prix_total_ht": prix_total_ht,
                    "montant_local": prix_total_ht,
                    "montant_import": self._valeur_numerique(capex.get("PRIX_IMPORT_TTC")),
                    "taux_economie": (
                        self._valeur_numerique(capex.get("ECONOMIE_NETTE")) / prix_total_ht
                        if prix_total_ht
                        else 0
                    ),
                    "capex_optimise": self._valeur_numerique(capex.get("CAPEX_OPTIMISE", prix_total_ht)),
                    "economie_nette": capex.get("ECONOMIE_NETTE", 0),
                    "decision_import": capex.get("DECISION", "LOCAL"),
                    "statut_ligne": ligne.get("statut_ligne", ""),
                }
            )

        ecrire_csv(self.chemins["fact_metre"], fact_metre)
        ecrire_csv(self.chemins["dim_famille"], familles.values())

    def _generer_audit_qualite(self, lignes_dqe: list[dict[str, Any]]) -> None:
        try:
            from openpyxl import Workbook
        except ImportError:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Audit qualite DQE"
        champs = [
            "id_ligne",
            "designation",
            "lot",
            "famille",
            "niveau",
            "type_zone",
            "quantite",
            "prix_total_ht",
            "statut_ligne",
        ]
        ws.append(champs)
        for ligne in lignes_dqe:
            if ligne.get("statut_ligne") != "OK":
                ws.append([ligne.get(champ, "") for champ in champs])
        if ws.max_row == 1:
            ws.append(["-", "Aucune anomalie critique", "-", "-", "-", "-", 0, 0, "OK"])
        self.chemins["audit"].parent.mkdir(parents=True, exist_ok=True)
        wb.save(self.chemins["audit"])

    def _resume(self, lignes_dqe: list[dict[str, Any]], lignes_capex: list[dict[str, Any]]) -> dict[str, Any]:
        montant_local = sum(self._valeur_numerique(ligne.get("MONTANT_LOCAL")) for ligne in lignes_capex)
        capex_optimise = sum(self._valeur_numerique(ligne.get("CAPEX_OPTIMISE")) for ligne in lignes_capex)
        return {
            "lignes_dqe": len(lignes_dqe),
            "montant_local": round(montant_local, 2),
            "capex_optimise": round(capex_optimise, 2),
            "economie_nette": round(montant_local - capex_optimise, 2),
            "sorties": {nom: str(chemin) for nom, chemin in self.chemins.items() if nom not in {"source", "parametres"}}
        }

    def _categorie_achat(self, famille: str) -> str:
        """Classe une famille pour les filtres Power BI et les arbitrages achats."""
        if famille == "gros_oeuvre":
            return "LOCAL_DOMINANT"
        if famille in self.FAMILLES_TECHNIQUES_IMPORTABLES:
            return "IMPORTABLE"
        return "A_ANALYSER"

    def _valeur_numerique(self, valeur: Any) -> float:
        """Convertit une valeur en nombre sans faire echouer tout le pipeline."""
        try:
            return float(valeur or 0)
        except (TypeError, ValueError):
            return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline complet SP2I CAPEX")
    parser.add_argument("--base-dir", default=None)
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve() if args.base_dir else None
    resultat = PipelineCompletSP2I(base_dir).executer()
    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
