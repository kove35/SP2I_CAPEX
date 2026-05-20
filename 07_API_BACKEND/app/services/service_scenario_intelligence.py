from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.core.scenario_analytics_engine import ScenarioAnalyticsEngine
from app.core.scenario_benchmark_engine import ScenarioBenchmarkEngine
from app.core.scenario_comparison_engine import ScenarioComparisonEngine
from app.core.scenario_history_engine import ScenarioHistoryEngine
from app.repositories.scenario_snapshot_repository import ScenarioSnapshotRepository


class ServiceScenarioIntelligence:
    def __init__(self, db: Session) -> None:
        repository = ScenarioSnapshotRepository(db)
        self.comparison_engine = ScenarioComparisonEngine(repository)
        self.benchmark_engine = ScenarioBenchmarkEngine(repository)
        self.analytics_engine = ScenarioAnalyticsEngine(repository)
        self.history_engine = ScenarioHistoryEngine(repository)

    def list_history(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return {
            "status": "SUCCESS",
            "history": self.history_engine.get_history(limit=limit, offset=offset),
        }

    def compare_scenarios(self, scenario_a: str, scenario_b: str) -> dict[str, Any]:
        comparison = self.comparison_engine.compare(scenario_a, scenario_b)
        return {
            "status": "SUCCESS",
            "scenario_a": scenario_a,
            "scenario_b": scenario_b,
            "comparison": comparison,
        }

    def best_scenarios(self, scenario_ids: list[str] | None = None, limit: int = 5) -> dict[str, Any]:
        ranking = self.benchmark_engine.rank_scenarios(scenario_ids=scenario_ids, limit=limit)
        return {
            "status": "SUCCESS",
            "best": ranking.get("best", {}),
            "rankings": ranking.get("rankings", []),
            "benchmarks": ranking.get("benchmarks", {}),
        }

    def analytics(self, scenario_id: str) -> dict[str, Any]:
        analytics = self.analytics_engine.analytics(scenario_id)
        return {
            "status": "SUCCESS",
            "scenario_id": scenario_id,
            "analytics": analytics,
        }
