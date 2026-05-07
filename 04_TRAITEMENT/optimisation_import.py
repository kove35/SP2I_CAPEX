from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from utils.clean_numbers import arrondir_montant, nettoyer_nombre
from utils.helpers import ecrire_csv, extraire_lignes, lire_json


class OptimiseurImport:
    """Calcule le meilleur arbitrage CAPEX entre achat local et import."""

    RATIOS_FOB = {
        "alucobond": 0.6,
        "ascenseur": 0.8,
        "climatisation": 0.7,
        "electricite": 0.5,
        "gros_oeuvre": 0.55,
        "menuiserie": 0.6,
        "peinture": 0.5,
        "plomberie": 0.5,
        "default": 0.5
    }

    def __init__(self, parametres: dict[str, Any] | None = None) -> None:
        parametres = parametres or {}
        self.taux = parametres.get(
            "taux_landed_cost",
            {
                "transport_maritime": 0.15,
                "assurance": 0.02,
                "droits_douane": 0.2,
                "frais_portuaires": 0.1,
                "logistique_locale": 0.05
            },
        )
        self.seuil_decision_import = float(parametres.get("seuil_decision_import", 0.97))

    def optimiser_fichier(self, entree: str | Path, sortie: str | Path) -> list[dict[str, Any]]:
        lignes = self.optimiser_lignes(extraire_lignes(lire_json(entree)))
        ecrire_csv(sortie, lignes)
        return lignes

    def optimiser_lignes(self, lignes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.optimiser_ligne(ligne) for ligne in lignes if ligne.get("designation")]

    def optimiser_ligne(self, ligne: dict[str, Any]) -> dict[str, Any]:
        famille = str(ligne.get("famille") or "default").lower().strip()
        quantite = nettoyer_nombre(ligne.get("quantite"), 1) or 1
        montant_local = nettoyer_nombre(ligne.get("prix_total_ht"), 0) or 0
        pu_local = montant_local / quantite if quantite else 0

        fob_unitaire = nettoyer_nombre(ligne.get("prix_fob"), None)
        if fob_unitaire is None:
            fob_unitaire = self.estimer_fob_unitaire(pu_local, famille)

        import_unitaire = self.calculer_landed_cost_unitaire(fob_unitaire)
        capex_import = import_unitaire * quantite
        decision = "IMPORT" if capex_import < montant_local * self.seuil_decision_import else "LOCAL"
        capex_optimise = capex_import if decision == "IMPORT" else montant_local
        economie = montant_local - capex_optimise

        return {
            "id_ligne": ligne.get("id_ligne", ""),
            "designation": ligne.get("designation", ""),
            "lot": ligne.get("lot", ""),
            "famille": famille,
            "QTE": round(quantite, 4),
            "PU_LOCAL": arrondir_montant(pu_local),
            "MONTANT_LOCAL": arrondir_montant(montant_local),
            "FOB_UNITAIRE": arrondir_montant(fob_unitaire),
            "IMPORT_UNITAIRE": arrondir_montant(import_unitaire),
            "PRIX_IMPORT_TTC": arrondir_montant(capex_import),
            "CAPEX_OPTIMISE": arrondir_montant(capex_optimise),
            "ECONOMIE_NETTE": arrondir_montant(economie),
            "TAUX_IMPORT": round(import_unitaire / pu_local, 4) if pu_local else 0,
            "DECISION": decision,
            "CLE_ANALYSE": f"{famille}|{decision}"
        }

    def estimer_fob_unitaire(self, pu_local: float, famille: str) -> float:
        ratio = self.RATIOS_FOB.get(famille, self.RATIOS_FOB["default"])
        coefficient_risque = 1.1
        return pu_local * ratio * coefficient_risque

    def calculer_landed_cost_unitaire(self, fob_unitaire: float) -> float:
        return fob_unitaire * (1 + sum(float(taux) for taux in self.taux.values()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimisation import SP2I")
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--parametres", "-p", default="01_PARAMETRES/parametres_import_pointe_noire.json")
    args = parser.parse_args()

    parametres = lire_json(args.parametres) if Path(args.parametres).exists() else {}
    lignes = OptimiseurImport(parametres).optimiser_fichier(args.input, args.output)
    total = sum(ligne["CAPEX_OPTIMISE"] for ligne in lignes)
    print(f"Optimisation terminee: {len(lignes)} lignes, CAPEX optimise {total:,.0f}")


if __name__ == "__main__":
    main()
