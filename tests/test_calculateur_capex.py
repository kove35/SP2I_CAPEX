"""
Tests unitaires du moteur pur `CalculateurCAPEX`.

Ces tests ne demarrent ni FastAPI ni PostgreSQL. Ils verifient uniquement les
formules metier de base : import, local, economie et decision.
"""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.calculator import CalculateurCAPEX


class CalculateurCAPEXTest(unittest.TestCase):
    def test_calcul_import_et_economie(self) -> None:
        """Une ligne importable doit produire un CAPEX optimise inferieur au local."""
        calculateur = CalculateurCAPEX(
            {
                "taux_landed_cost": {
                    "transport_maritime": 0.10,
                    "assurance": 0.02,
                    "droits_douane": 0.10,
                },
                "seuil_decision_import": 0.97,
                "coefficient_risque": 1.0,
            }
        )

        ligne = calculateur.optimiser_ligne(
            {
                "id_ligne": "L1",
                "designation": "Cable electrique",
                "famille": "electricite",
                "quantite": 10,
                "prix_total_ht": 1000,
            }
        )

        self.assertEqual(ligne["CAPEX_LOCAL"], 1000)
        self.assertEqual(ligne["DECISION_IMPORT"], "IMPORT")
        self.assertLess(ligne["CAPEX_IMPORT"], ligne["CAPEX_LOCAL"])
        self.assertEqual(ligne["CAPEX_OPTIMISE"], ligne["CAPEX_IMPORT"])
        self.assertAlmostEqual(ligne["ECONOMIE_NETTE"], 390.0, places=2)

    def test_decision_local_si_gain_insuffisant(self) -> None:
        """Le seuil evite de choisir IMPORT quand l'ecart est trop faible."""
        calculateur = CalculateurCAPEX(
            {
                "taux_landed_cost": {"transport_maritime": 0.0},
                "seuil_decision_import": 0.50,
                "coefficient_risque": 1.0,
            }
        )

        ligne = calculateur.optimiser_ligne(
            {
                "designation": "Menuiserie",
                "famille": "menuiserie",
                "quantite": 1,
                "prix_total_ht": 1000,
            }
        )

        self.assertEqual(ligne["DECISION_IMPORT"], "LOCAL")
        self.assertEqual(ligne["CAPEX_OPTIMISE"], 1000)
        self.assertEqual(ligne["ECONOMIE_NETTE"], 0)

    def test_fob_fourni_est_prioritaire(self) -> None:
        """Quand un prix FOB est fourni, le moteur ne l'estime pas."""
        ligne = CalculateurCAPEX({"taux_landed_cost": {"transport": 0.10}}).optimiser_ligne(
            {
                "designation": "Ascenseur",
                "famille": "ascenseur",
                "quantite": 2,
                "prix_total_ht": 10000,
                "prix_fob": 1000,
            }
        )

        self.assertEqual(ligne["FOB_UNITAIRE"], 1000)
        self.assertEqual(ligne["PU_IMPORT_HT"], 1100)
        self.assertEqual(ligne["CAPEX_IMPORT"], 2200)

    def test_kpi_utilise_ratio_des_totaux(self) -> None:
        """Le taux economie global est le ratio des totaux, pas une moyenne."""
        calculateur = CalculateurCAPEX()
        kpi = calculateur.calculer_kpi(
            [
                {"CAPEX_LOCAL": 1000, "CAPEX_OPTIMISE": 900, "ECONOMIE_NETTE": 100, "DECISION": "IMPORT"},
                {"CAPEX_LOCAL": 100, "CAPEX_OPTIMISE": 0, "ECONOMIE_NETTE": 100, "DECISION": "IMPORT"},
            ]
        )

        self.assertEqual(kpi["capex_local"], 1100)
        self.assertEqual(kpi["economie_nette"], 200)
        self.assertEqual(kpi["taux_economie"], 0.1818)

    def test_valeurs_invalides_ne_font_pas_crasher_le_calculateur(self) -> None:
        """Le calculateur reste tolerant ; la validation stricte vit dans DataCleaner."""
        ligne = CalculateurCAPEX().optimiser_ligne(
            {
                "designation": "Prix invalide",
                "famille": "inconnue",
                "quantite": "abc",
                "prix_total_ht": None,
            }
        )

        self.assertEqual(ligne["QTE"], 1)
        self.assertEqual(ligne["CAPEX_LOCAL"], 0)
        self.assertEqual(ligne["famille"], "inconnue")


if __name__ == "__main__":
    unittest.main()
