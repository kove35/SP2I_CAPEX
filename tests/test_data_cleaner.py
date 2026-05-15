"""
Tests unitaires de `DataCleaner`.

Le cleaner protege le moteur contre les formats Excel/DQE heterogenes. Les
tests montrent la difference entre mode tolerant et mode strict.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.cleaner import DataCleaner, clean_famille, clean_lot, clean_niveau, nettoyer_nombre
from app.core.errors import DataQualityError


class DataCleanerTest(unittest.TestCase):
    def test_nettoyer_nombre_formats_metier(self) -> None:
        self.assertEqual(nettoyer_nombre("1 234,50 FCFA"), 1234.5)
        self.assertEqual(nettoyer_nombre(""), None)
        self.assertEqual(nettoyer_nombre("abc", 0), 0)

    def test_clean_lot_preserve_numero(self) -> None:
        self.assertEqual(clean_lot("LOT1"), "LOT 1")
        self.assertEqual(clean_lot("Lot 4 : Electricite"), "LOT 4 : ELECTRICITE")
        self.assertEqual(clean_lot(" lot 12 "), "LOT 12")

    def test_clean_famille_et_niveau(self) -> None:
        self.assertEqual(clean_famille("Gros Œuvre"), "gros_uvre")
        self.assertEqual(clean_niveau("rdc"), "RDC")
        self.assertEqual(clean_niveau("Etage 2"), "ETAGE 2")

    def test_mode_tolerant_conserve_ligne_avec_warning(self) -> None:
        cleaner = DataCleaner(mode="tolerant")
        lignes = cleaner.normaliser_lignes(
            [
                {
                    "designation": "Poste sans prix",
                    "quantite": 1,
                    "prix_total_ht": 0,
                    "lot": "Lot 1",
                }
            ]
        )

        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0]["statut_ligne"], "PRIX_UNITAIRE_INVALIDE|PRIX_TOTAL_INVALIDE")
        self.assertTrue(cleaner.warnings)

    def test_mode_strict_refuse_ligne_invalide(self) -> None:
        cleaner = DataCleaner(mode="strict")

        with self.assertRaises(DataQualityError):
            cleaner.normaliser_lignes(
                [
                    {
                        "designation": "Poste sans prix",
                        "quantite": 1,
                        "prix_total_ht": 0,
                        "lot": "Lot 1",
                    }
                ]
            )

    def test_contexte_lot_est_preserve(self) -> None:
        cleaner = DataCleaner(mode="tolerant")
        lignes = cleaner.normaliser_lignes(
            [
                {"designation": "Header lot", "lot": "Lot 7", "quantite": 1, "prix_total_ht": 1},
                {"designation": "Cable", "quantite": 2, "prix_total_ht": 200},
            ]
        )

        self.assertEqual(lignes[1]["lot"], "LOT 7")


if __name__ == "__main__":
    unittest.main()
