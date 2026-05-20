from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_API_BACKEND"))

from app.core.anomaly_detection_engine import AnomalyDetectionEngine


class AnomalyDetectionEngineTest(unittest.TestCase):
    def test_detects_lost_zeros_against_reference(self) -> None:
        engine = AnomalyDetectionEngine()
        anomalies = engine.detect_line_anomalies(
            {"designation": "Groupe electrogene 60 KVA", "prix_total_ht": 150000},
            {"price_min": 15000000, "price_max": 40000000},
        )

        self.assertIn("LOST_ZEROS_SUSPECTED", [item["code"] for item in anomalies])
        self.assertGreater(engine.score_anomalies(anomalies), 0)

    def test_detects_statistical_outlier(self) -> None:
        result = AnomalyDetectionEngine().detect_price_outliers([
            {"designation": "A", "prix_total_ht": 100},
            {"designation": "B", "prix_total_ht": 105},
            {"designation": "C", "prix_total_ht": 98},
            {"designation": "D", "prix_total_ht": 102},
            {"designation": "E", "prix_total_ht": 10000},
        ])

        self.assertGreaterEqual(result["count"], 1)


if __name__ == "__main__":
    unittest.main()
