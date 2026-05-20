from __future__ import annotations

from typing import Any

from app.repositories.scenario_snapshot_repository import ScenarioSnapshotRepository


class ScenarioAnalyticsEngine:
    def __init__(self, snapshot_repository: ScenarioSnapshotRepository) -> None:
        self.snapshot_repository = snapshot_repository

    def analytics(self, scenario_id: str) -> dict[str, Any]:
        snapshot = self.snapshot_repository.get_scenario_aggregates(scenario_id)
        timeline = self.snapshot_repository.get_scenario_timeline(scenario_id)
        if not snapshot:
            return {"error": "Scenario not found."}

        return {
            "scenario": snapshot,
            "timeline": timeline,
            "trend": self._build_trend(snapshot, timeline),
            "score_breakdown": self._build_score_breakdown(snapshot),
        }

    def _build_trend(self, snapshot: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "current_global_score": self._build_global_score(snapshot),
            "timeline_points": [
                {
                    "periode": point.get("periode"),
                    "capex_optimise": point.get("capex_optimise"),
                    "economie_nette": point.get("economie_nette"),
                    "decision_score_average": point.get("decision_score_average"),
                    "risk_score_average": point.get("risk_score_average"),
                }
                for point in timeline
            ],
        }

    def _build_score_breakdown(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        return {
            "savings_ratio": self._savings_ratio(snapshot),
            "decision_quality": snapshot.get("decision_score_average"),
            "risk_quality": max(0.0, 100.0 - float(snapshot.get("risk_score_average") or 0)),
            "logistics_performance": snapshot.get("lead_time_score_average"),
            "procurement_health": max(0.0, 100.0 - float(snapshot.get("moq_risk_score_average") or 0)),
            "global_score": self._build_global_score(snapshot),
        }

    def _savings_ratio(self, snapshot: dict[str, Any]) -> float:
        capex_local = float(snapshot.get("capex_local") or 0)
        economie = float(snapshot.get("economie_nette") or 0)
        return round((economie / capex_local * 100) if capex_local else 0.0, 2)

    def _build_global_score(self, snapshot: dict[str, Any]) -> float:
        capex_local = float(snapshot.get("capex_local") or 0)
        economie = float(snapshot.get("economie_nette") or 0)
        savings_ratio = (economie / capex_local * 100) if capex_local else 0.0
        decision_score = float(snapshot.get("decision_score_average") or 0)
        risk_score = float(snapshot.get("risk_score_average") or 0)
        lead_time_score = float(snapshot.get("lead_time_score_average") or 0)
        moq_risk = float(snapshot.get("moq_risk_score_average") or 0)

        return round(
            max(0.0,
                min(
                    100.0,
                    0.3 * min(savings_ratio, 100)
                    + 0.25 * decision_score
                    + 0.2 * max(0.0, 100.0 - risk_score)
                    + 0.15 * lead_time_score
                    + 0.1 * max(0.0, 100.0 - moq_risk)
                )
            ),
            2,
        )
