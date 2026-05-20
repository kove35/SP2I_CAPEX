from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.repository_run import RepositoryRun
from app.repositories.repository_scenario import RepositoryScenario
from app.repositories.repository_simulation import RepositorySimulation


class ScenarioPersistenceEngine:
    """Gestion de la persistence et du cycle de vie des scenarios et simulations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._scenario_repo = RepositoryScenario(db)
        self._simulation_repo = RepositorySimulation(db)
        self._run_repo = RepositoryRun(db)

    def persist_scenario(
        self,
        scenario_name: str,
        scenario_type: str,
        parameters: dict[str, Any],
        created_by: str,
        scenario_id: str,
        run_id: str,
        simulation_id: str,
        lignes: list[dict[str, Any]],
        description: str = "",
        is_baseline: bool = False,
        warnings: list[Any] | None = None,
        errors: list[Any] | None = None,
        duration_ms: int = 0,
        status: str = "SUCCESS",
    ) -> dict[str, Any]:
        self._scenario_repo.create_scenario(
            scenario_id=scenario_id,
            scenario_nom=scenario_name,
            scenario_type=scenario_type,
            description=description,
            parameters=parameters,
            is_baseline=is_baseline,
            created_by=created_by,
        )
        self._run_repo.create_run(
            run_id=run_id,
            scenario_id=scenario_id,
            rows_in=len(lignes),
            source_type="API",
        )
        rows_out = self._simulation_repo.save_simulation_lines(
            simulation_id=simulation_id,
            scenario_id=scenario_id,
            run_id=run_id,
            lignes=lignes,
        )
        self._run_repo.complete_run(
            run_id=run_id,
            rows_out=rows_out,
            rows_rejected=max(len(lignes) - rows_out, 0),
            warnings=warnings or [],
            errors=errors or [],
            duration_ms=duration_ms,
            status=status,
        )
        self.db.commit()
        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "scenario_type": scenario_type,
            "rows_out": rows_out,
        }

    def get_scenario_snapshot(self, scenario_id: str, limit: int = 500, offset: int = 0) -> dict[str, Any]:
        scenario = self._scenario_repo.get_scenario(scenario_id)
        if not scenario:
            return {}
        lines = self._simulation_repo.get_simulation(scenario_id, limit=limit, offset=offset)
        return {"scenario": scenario, "lines": lines}

    def compare_scenarios(self, scenario_a: str, scenario_b: str) -> list[dict[str, Any]]:
        return self._simulation_repo.compare_simulations(scenario_a, scenario_b)

    def rollback_scenario(self, scenario_id: str) -> dict[str, Any]:
        snapshot = self.get_scenario_snapshot(scenario_id)
        return {
            "scenario_id": scenario_id,
            "scenario": snapshot.get("scenario", {}),
            "lines": snapshot.get("lines", []),
            "can_rollback": bool(snapshot.get("scenario")),
        }
