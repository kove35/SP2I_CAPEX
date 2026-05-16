from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.ai.ai_anomaly_detector import AIAnomalyDetector


class AIAnomalyDetectorTest(unittest.TestCase):
    def test_detecte_quantite_incoherente(self) -> None:
        detector = AIAnomalyDetector()

        anomalies = detector.detect(
            [
                {
                    "id_ligne": "L1",
                    "designation": "Cable",
                    "quantite": 0,
                    "prix_unitaire_ht": 1000,
                    "prix_total_ht": 0,
                    "famille_ai": "ELECTRICITE",
                }
            ]
        )

        self.assertTrue(any(item["anomaly_type"] == "quantite_incoherente" for item in anomalies))


if __name__ == "__main__":
    unittest.main()
