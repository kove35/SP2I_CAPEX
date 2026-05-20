from __future__ import annotations

from typing import Any

from app.repositories.scenario_snapshot_repository import ScenarioSnapshotRepository


class ScenarioHistoryEngine:
    def __init__(self, snapshot_repository: ScenarioSnapshotRepository) -> None:
        self.snapshot_repository = snapshot_repository

    def get_history(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        return self.snapshot_repository.list_scenario_history(limit=limit, offset=offset)

    def get_snapshot(self, scenario_id: str) -> dict[str, Any]:
        return self.snapshot_repository.get_scenario_snapshot(scenario_id)

    def get_timeline(self, scenario_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.snapshot_repository.get_scenario_timeline(scenario_id, limit=limit)
