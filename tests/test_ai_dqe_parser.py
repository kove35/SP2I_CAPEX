from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.ai.ai_dqe_parser import AIDQEParser


class AIDQEParserTest(unittest.TestCase):
    def test_preserve_contexte_lot_pour_articles_suivants(self) -> None:
        parser = AIDQEParser()
        rows = [
            ["Lot", "Designation", "QTE", "PU", "Montant"],
            ["LOT 4 : ELECTRICITE", "", "", "", ""],
            ["", "Cable principal", 20, 5000, 100000],
        ]
        analysis = {
            "ligne_entete": 1,
            "mapping": [
                {"champ_standard": "lot", "colonne_index": 0},
                {"champ_standard": "designation", "colonne_index": 1},
                {"champ_standard": "quantite", "colonne_index": 2},
                {"champ_standard": "prix_unitaire_ht", "colonne_index": 3},
                {"champ_standard": "prix_total_ht", "colonne_index": 4},
            ],
        }

        normalized, classified = parser.parse_rows(rows, analysis)

        self.assertEqual(classified[0]["row_type"], "lot")
        self.assertEqual(classified[0]["governance_status"], "IGNORED")
        self.assertEqual(classified[0]["certification_status"], "IGNORED_NOT_A_LOSS")
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["lot"], "LOT 4 : ELECTRICITE")
        self.assertEqual(normalized[0]["governance_status"], "VALID")

    def test_review_required_n_est_pas_data_loss(self) -> None:
        parser = AIDQEParser()
        rows = [
            ["Designation", "QTE", "PU", "Montant"],
            ["Pompe de relevage", 1, 250000, 250000],
        ]
        analysis = {
            "ligne_entete": 1,
            "mapping": [
                {"champ_standard": "designation", "colonne_index": 0},
                {"champ_standard": "quantite", "colonne_index": 1},
                {"champ_standard": "prix_unitaire_ht", "colonne_index": 2},
                {"champ_standard": "prix_total_ht", "colonne_index": 3},
            ],
        }

        normalized, classified = parser.parse_rows(rows, analysis)

        self.assertEqual(len(normalized), 0)
        self.assertEqual(classified[0]["row_type"], "inconnu")
        self.assertEqual(classified[0]["governance_status"], "REVIEW_REQUIRED")
        self.assertTrue(classified[0]["review_required"])
        self.assertFalse(any(issue["category"] == "DATA_LOSS" for issue in classified[0]["governance_issues"]))


if __name__ == "__main__":
    unittest.main()
