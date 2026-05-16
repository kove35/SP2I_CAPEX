from __future__ import annotations

from statistics import median

from app.core import nettoyer_nombre


class AIAnomalyDetector:
    """Detecte des anomalies simples et explicables sur les lignes normalisees."""

    def detect(self, rows: list[dict]) -> list[dict]:
        anomalies: list[dict] = []
        prices_by_family = self._prices_by_family(rows)

        seen_line_signatures: set[tuple[str, str, float, float]] = set()
        for index, row in enumerate(rows, start=1):
            line_id = row.get("id_ligne") or index
            designation = str(row.get("designation") or "").strip().lower()
            lot = str(row.get("lot") or "").strip().upper()
            quantity = nettoyer_nombre(row.get("quantite"), 0) or 0
            unit_price = nettoyer_nombre(row.get("prix_unitaire_ht"), 0) or 0
            total_price = nettoyer_nombre(row.get("prix_total_ht"), 0) or 0
            family = row.get("famille_ai") or row.get("famille") or "INCONNUE"

            if quantity <= 0:
                anomalies.append(self._anomaly(line_id, "quantite_incoherente", 0.9, "Quantite absente ou inferieure a zero."))
            if unit_price <= 0 and total_price <= 0:
                anomalies.append(self._anomaly(line_id, "prix_absent", 0.86, "Aucun prix exploitable detecte."))
            signature = (lot, designation, round(quantity, 4), round(total_price, 2))
            if signature in seen_line_signatures and designation:
                anomalies.append(
                    self._anomaly(
                        line_id,
                        "doublon_possible",
                        0.82,
                        "Meme lot, designation, quantite et montant deja rencontres.",
                    )
                )
            seen_line_signatures.add(signature)

            reference_price = prices_by_family.get(str(family))
            if reference_price and unit_price > reference_price * 10:
                anomalies.append(
                    self._anomaly(
                        line_id,
                        "prix_anormal",
                        0.91,
                        "Prix unitaire plus de 10x superieur a la mediane de la famille.",
                    )
                )

        return anomalies

    def _prices_by_family(self, rows: list[dict]) -> dict[str, float]:
        values: dict[str, list[float]] = {}
        for row in rows:
            family = str(row.get("famille_ai") or row.get("famille") or "INCONNUE")
            unit_price = nettoyer_nombre(row.get("prix_unitaire_ht"), 0) or 0
            if unit_price > 0:
                values.setdefault(family, []).append(unit_price)
        return {family: median(prices) for family, prices in values.items() if prices}

    def _anomaly(self, line_id: object, anomaly_type: str, confidence: float, reason: str) -> dict:
        return {
            "line_id": line_id,
            "anomaly_type": anomaly_type,
            "confidence": confidence,
            "reason": reason,
        }
