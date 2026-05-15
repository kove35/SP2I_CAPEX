from __future__ import annotations

from typing import Any

from app.core.cleaner import arrondir_montant, nettoyer_nombre
from app.core.global_parameters import (
    DEFAULT_COEFFICIENT_RISQUE,
    DEFAULT_RATIOS_FOB,
    DEFAULT_SEUIL_DECISION_IMPORT,
    DEFAULT_TAUX_LANDED_COST,
)


class CalculateurCAPEX:
    """
    Moteur pur de calcul CAPEX import/local.

    Aucune dependance a pandas, FastAPI ou SQLAlchemy ici. Le moteur temps reel
    doit rester leger : des dictionnaires en entree, des dictionnaires en sortie.
    """

    RATIOS_FOB = DEFAULT_RATIOS_FOB
    TAUX_LANDED_COST_DEFAUT = DEFAULT_TAUX_LANDED_COST

    def __init__(self, parametres: dict[str, Any] | None = None) -> None:
        parametres = parametres or {}
        self.taux = parametres.get("taux_landed_cost", self.TAUX_LANDED_COST_DEFAUT)
        self.seuil_decision_import = float(parametres.get("seuil_decision_import", DEFAULT_SEUIL_DECISION_IMPORT))
        self.coefficient_risque = float(parametres.get("coefficient_risque", DEFAULT_COEFFICIENT_RISQUE))

    def optimiser_lignes(self, lignes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.optimiser_ligne(ligne) for ligne in lignes if ligne.get("designation")]

    def optimiser_ligne(self, ligne: dict[str, Any]) -> dict[str, Any]:
        famille = str(ligne.get("famille") or "default").lower().strip()
        quantite = nettoyer_nombre(ligne.get("quantite"), 1) or 1
        montant_local = nettoyer_nombre(ligne.get("prix_total_ht") or ligne.get("montant_local"), 0) or 0
        pu_local = montant_local / quantite if quantite else 0

        fob_unitaire = nettoyer_nombre(ligne.get("prix_fob"), None)
        if fob_unitaire is None:
            fob_unitaire = self.estimer_fob_unitaire(pu_local, famille)

        import_unitaire = self.calculer_landed_cost_unitaire(fob_unitaire)
        capex_import = import_unitaire * quantite
        decision = "IMPORT" if capex_import < montant_local * self.seuil_decision_import else "LOCAL"
        capex_optimise = capex_import if decision == "IMPORT" else montant_local
        economie = montant_local - capex_optimise
        taux_import = import_unitaire / pu_local if pu_local else 0
        taux_economie = economie / montant_local if montant_local else 0

        return {
            "id_ligne": ligne.get("id_ligne", ""),
            "designation": ligne.get("designation", ""),
            "lot": ligne.get("lot", ""),
            "famille": famille,
            "batiment": ligne.get("batiment", ""),
            "niveau": ligne.get("niveau", ""),
            "statut_ligne": ligne.get("statut_ligne", "OK"),
            "QTE": round(quantite, 4),
            "PU_LOCAL": arrondir_montant(pu_local),
            "MONTANT_LOCAL": arrondir_montant(montant_local),
            "FOB_UNITAIRE": arrondir_montant(fob_unitaire),
            "IMPORT_UNITAIRE": arrondir_montant(import_unitaire),
            "PU_IMPORT_HT": arrondir_montant(import_unitaire),
            "CAPEX_IMPORT": arrondir_montant(capex_import),
            "CAPEX_LOCAL": arrondir_montant(montant_local),
            "PRIX_IMPORT_TTC": arrondir_montant(capex_import),
            "CAPEX_OPTIMISE": arrondir_montant(capex_optimise),
            "ECONOMIE_NETTE": arrondir_montant(economie),
            "TAUX_IMPORT": round(taux_import, 4),
            "TAUX_ECONOMIE": round(taux_economie, 4),
            "DECISION": decision,
            "DECISION_IMPORT": decision,
            "SCORE_CONFIANCE": self.scorer_confiance(ligne, taux_import),
            "CLE_ANALYSE": f"{famille}|{decision}",
        }

    def calculer_kpi(self, lignes: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Agrege les KPI API avec Python natif.

        Pandas reste utile pour l'ETL lourd, mais ces sommes simples ne doivent
        pas imposer une dependance couteuse au chemin API temps reel.
        """
        capex_local = sum(nettoyer_nombre(ligne.get("CAPEX_LOCAL") or ligne.get("MONTANT_LOCAL"), 0) or 0 for ligne in lignes)
        capex_import = sum(nettoyer_nombre(ligne.get("CAPEX_IMPORT") or ligne.get("PRIX_IMPORT_TTC"), 0) or 0 for ligne in lignes)
        capex_optimise = sum(nettoyer_nombre(ligne.get("CAPEX_OPTIMISE"), 0) or 0 for ligne in lignes)
        economie = sum(nettoyer_nombre(ligne.get("ECONOMIE_NETTE"), 0) or 0 for ligne in lignes)
        import_count = sum(1 for ligne in lignes if ligne.get("DECISION_IMPORT") == "IMPORT" or ligne.get("DECISION") == "IMPORT")

        return {
            "lignes": len(lignes),
            "capex_local": round(capex_local, 2),
            "capex_import": round(capex_import, 2),
            "capex_optimise": round(capex_optimise, 2),
            "economie_nette": round(economie, 2),
            "taux_economie": round(economie / capex_local, 4) if capex_local else 0,
            "lignes_import": import_count,
            "lignes_local": len(lignes) - import_count,
        }

    def analyse_sensibilite(self, lignes: list[dict[str, Any]], variations: list[float]) -> list[dict[str, Any]]:
        scenarios: list[dict[str, Any]] = []
        for variation in variations:
            parametres = {
                "taux_landed_cost": {
                    nom: float(taux) * (1 + variation)
                    for nom, taux in self.taux.items()
                },
                "seuil_decision_import": self.seuil_decision_import,
            }
            lignes_scenario = CalculateurCAPEX(parametres).optimiser_lignes(lignes)
            scenarios.append({"variation": variation, "kpi": self.calculer_kpi(lignes_scenario)})
        return scenarios

    def estimer_fob_unitaire(self, pu_local: float, famille: str) -> float:
        ratio = self.RATIOS_FOB.get(famille, self.RATIOS_FOB["default"])
        return pu_local * ratio * self.coefficient_risque

    def calculer_landed_cost_unitaire(self, fob_unitaire: float) -> float:
        return fob_unitaire * (1 + sum(float(taux) for taux in self.taux.values()))

    def scorer_confiance(self, ligne: dict[str, Any], taux_import: float) -> float:
        score = 0.75
        if ligne.get("prix_fob"):
            score += 0.15
        if ligne.get("famille") and ligne.get("famille") != "default":
            score += 0.05
        if 0.3 <= taux_import <= 1.5:
            score += 0.05
        return round(min(score, 1.0), 2)
