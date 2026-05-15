from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


class RepositoryScenario:
    """
    Repository des scenarios CAPEX.

    Il isole la persistence PostgreSQL de `ServiceSimulation`. Le service pense
    en cas d'usage, le repository pense en tables et requetes.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_scenario(
        self,
        scenario_nom: str,
        scenario_type: str,
        parameters: dict[str, Any],
        projet_id: int | None = None,
        description: str = "",
        is_baseline: bool = False,
        created_by: str = "system",
        scenario_id: str | None = None,
    ) -> str:
        scenario_uuid = str(UUID(scenario_id)) if scenario_id else str(uuid4())
        row = self.db.execute(
            text(
                """
                INSERT INTO dim_scenario (
                    scenario_id,
                    projet_id,
                    scenario_nom,
                    scenario_type,
                    description,
                    parameters_json,
                    is_baseline,
                    created_by
                )
                VALUES (
                    :scenario_id,
                    COALESCE(:projet_id, (SELECT projet_id FROM dim_projet ORDER BY projet_id LIMIT 1)),
                    :scenario_nom,
                    :scenario_type,
                    :description,
                    CAST(:parameters_json AS jsonb),
                    :is_baseline,
                    :created_by
                )
                ON CONFLICT (scenario_id) DO UPDATE SET
                    scenario_nom = EXCLUDED.scenario_nom,
                    scenario_type = EXCLUDED.scenario_type,
                    description = EXCLUDED.description,
                    parameters_json = EXCLUDED.parameters_json,
                    is_baseline = EXCLUDED.is_baseline,
                    updated_at = now()
                RETURNING scenario_id::text
                """
            ),
            {
                "scenario_id": scenario_uuid,
                "projet_id": projet_id,
                "scenario_nom": scenario_nom,
                "scenario_type": scenario_type,
                "description": description,
                "parameters_json": json.dumps(parameters),
                "is_baseline": is_baseline,
                "created_by": created_by,
            },
        ).one()
        return str(row[0])

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT
                    scenario_id::text,
                    projet_id,
                    scenario_nom,
                    scenario_type,
                    description,
                    parameters_json,
                    is_baseline,
                    created_by,
                    created_at,
                    updated_at
                FROM dim_scenario
                WHERE scenario_id = CAST(:scenario_id AS uuid)
                """
            ),
            {"scenario_id": scenario_id},
        ).mappings().first()
        return dict(row) if row else None

    def list_scenarios(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    scenario_id::text,
                    scenario_nom,
                    scenario_type,
                    is_baseline,
                    created_by,
                    created_at,
                    updated_at
                FROM dim_scenario
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        ).mappings().all()
        return [dict(row) for row in rows]

    def update_scenario(self, scenario_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_scenario(scenario_id)
        if not current:
            return None

        scenario_nom = values.get("scenario_nom", current["scenario_nom"])
        scenario_type = values.get("scenario_type", current["scenario_type"])
        description = values.get("description", current["description"])
        is_baseline = values.get("is_baseline", current["is_baseline"])
        parameters = values.get("parameters_json", current["parameters_json"])

        self.create_scenario(
            scenario_id=scenario_id,
            scenario_nom=scenario_nom,
            scenario_type=scenario_type,
            description=description,
            is_baseline=is_baseline,
            parameters=parameters,
            created_by=current["created_by"],
            projet_id=current["projet_id"],
        )
        return self.get_scenario(scenario_id)
