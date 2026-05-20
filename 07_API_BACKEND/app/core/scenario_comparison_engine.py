from __future__ import annotations

from typing import Any

from app.repositories.scenario_snapshot_repository import ScenarioSnapshotRepository


class ScenarioComparisonEngine:
    def __init__(self, snapshot_repository: ScenarioSnapshotRepository) -> None:
        self.snapshot_repository = snapshot_repository

    def compare(self, scenario_a: str, scenario_b: str) -> dict[str, Any]:
        rows = self.snapshot_repository.compare_scenarios([scenario_a, scenario_b])
        if len(rows) < 2:
            return {"error": "One or both scenario IDs are missing or have no simulation data."}

        snapshots = [self._enrich_snapshot(row) for row in rows]
        ordered = sorted(snapshots, key=lambda entry: entry["global_score"], reverse=True)
        comparison = {
            "scenarios": snapshots,
            "winner": ordered[0]["scenario_id"],
            "best_scenario": ordered[0],
            "comparison_metrics": self._build_comparison(snapshots[0], snapshots[1]),
        }
        return comparison

    def _build_comparison(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        metrics = [
            "capex_local",
            "capex_optimise",
            "economie_nette",
            "decision_score_average",
            "risk_score_average",
            "lead_time_score_average",
            "cashflow_score_average",
            "moq_risk_score_average",
            "fill_rate_average",
        ]
        comparison = {}
        for metric in metrics:
            comparison[metric] = {
                "left": left.get(metric),
                "right": right.get(metric),
                "delta": self._delta(left.get(metric), right.get(metric)),
            }
        return comparison

    def _delta(self, left_value: Any, right_value: Any) -> float:
        if left_value is None or right_value is None:
            return 0.0
        try:
            return float(left_value) - float(right_value)
        except (TypeError, ValueError):
            return 0.0

    def _enrich_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        snapshot = dict(snapshot)
        snapshot["global_score"] = self._build_global_score(snapshot)
        snapshot["scenario_label"] = snapshot.get("scenario_nom") or snapshot.get("scenario_id")
        return snapshot

    def _build_global_score(self, snapshot: dict[str, Any]) -> float:
        capex_local = float(snapshot.get("capex_local") or 0)
        economie = float(snapshot.get("economie_nette") or 0)
        savings_ratio = (economie / capex_local * 100) if capex_local else 0.0
        decision_score = float(snapshot.get("decision_score_average") or 0)
        risk_score = float(snapshot.get("risk_score_average") or 0)
        lead_time_score = float(snapshot.get("lead_time_score_average") or 0)
        moq_risk = float(snapshot.get("moq_risk_score_average") or 0)

        score = (
            0.28 * min(savings_ratio, 100)
            + 0.22 * decision_score
            + 0.2 * max(0.0, 100.0 - risk_score)
            + 0.18 * lead_time_score
            + 0.12 * max(0.0, 100.0 - moq_risk)
        )
        return round(max(0.0, min(score, 100.0)), 2)
