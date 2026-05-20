from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


class AnomalyDetectionEngine:
    """Detecte les anomalies statistiques et metier sur les lignes CAPEX."""

    def detect_price_outliers(self, lines: list[dict[str, Any]], price_key: str = "prix_total_ht") -> dict[str, Any]:
        prices = [self._number(line.get(price_key), 0) for line in lines]
        prices = [price for price in prices if price > 0]
        z_scores = self._z_scores(prices)
        iqr = self._iqr_bounds(prices)
        outliers = []
        for index, line in enumerate(lines):
            price = self._number(line.get(price_key), 0)
            z_score = z_scores.get(price, 0.0)
            iqr_outlier = bool(iqr and (price < iqr["lower"] or price > iqr["upper"]))
            if abs(z_score) >= 2.5 or iqr_outlier:
                outliers.append({
                    "index": index,
                    "designation": line.get("designation"),
                    "price": price,
                    "z_score": round(z_score, 2),
                    "iqr_outlier": iqr_outlier,
                })
        return {
            "method": "Z_SCORE_IQR",
            "count": len(outliers),
            "outliers": outliers,
            "benchmark": {"mean": round(mean(prices), 2) if prices else 0.0, **(iqr or {})},
        }

    def detect_line_anomalies(self, line: dict[str, Any], reference: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        anomalies: list[dict[str, Any]] = []
        price = self._number(line.get("prix_total_ht") or line.get("CAPEX_LOCAL"), 0)
        quantity = self._number(line.get("quantite") or line.get("QTE"), 1)
        if price <= 0:
            anomalies.append({"code": "ZERO_OR_NEGATIVE_PRICE", "severity": "HIGH", "message": "Prix nul ou negatif."})
        if quantity <= 0:
            anomalies.append({"code": "INVALID_QUANTITY", "severity": "HIGH", "message": "Quantite nulle ou negative."})
        if reference:
            price_min = self._number(reference.get("price_min"), 0)
            price_max = self._number(reference.get("price_max"), 0)
            if price_min and price < price_min * 0.15:
                anomalies.append({"code": "LOST_ZEROS_SUSPECTED", "severity": "HIGH", "message": "Prix tres inferieur au referentiel, zeros perdus possibles."})
            elif price_min and price < price_min:
                anomalies.append({"code": "PRICE_BELOW_RANGE", "severity": "MEDIUM", "message": "Prix inferieur au range de reference."})
            if price_max and price > price_max:
                anomalies.append({"code": "PRICE_ABOVE_RANGE", "severity": "MEDIUM", "message": "Prix superieur au range de reference."})
        roi = self._number(line.get("ROI") or line.get("roi"), 0)
        if roi and (roi < -100 or roi > 500):
            anomalies.append({"code": "ABERRANT_ROI", "severity": "HIGH", "message": "ROI hors bornes realistes."})
        return anomalies

    def score_anomalies(self, anomalies: list[dict[str, Any]]) -> float:
        severity_weight = {"LOW": 10.0, "MEDIUM": 25.0, "HIGH": 45.0}
        return round(min(sum(severity_weight.get(item.get("severity", "LOW"), 10.0) for item in anomalies), 100.0), 2)

    def _z_scores(self, values: list[float]) -> dict[float, float]:
        if len(values) < 2:
            return {}
        avg = mean(values)
        std = pstdev(values) or 1.0
        return {value: (value - avg) / std for value in values}

    def _iqr_bounds(self, values: list[float]) -> dict[str, float]:
        if len(values) < 4:
            return {}
        ordered = sorted(values)
        q1 = ordered[len(ordered) // 4]
        q3 = ordered[(len(ordered) * 3) // 4]
        iqr = q3 - q1
        return {"lower": q1 - 1.5 * iqr, "upper": q3 + 1.5 * iqr}

    def _number(self, value: Any, default: float) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
