from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


class RepositoryRun:
    """Repository des executions de simulation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self,
        scenario_id: str,
        rows_in: int,
        projet_id: int | None = None,
        source_file: str = "",
        source_type: str = "API",
        run_id: str | None = None,
    ) -> str:
        run_uuid = str(UUID(run_id)) if run_id else str(uuid4())
        row = self.db.execute(
            text(
                """
                INSERT INTO simulation_run (
                    run_id,
                    scenario_id,
                    projet_id,
                    source_file,
                    source_type,
                    rows_in,
                    status
                )
                VALUES (
                    :run_id,
                    CAST(:scenario_id AS uuid),
                    COALESCE(:projet_id, (SELECT projet_id FROM dim_projet ORDER BY projet_id LIMIT 1)),
                    :source_file,
                    :source_type,
                    :rows_in,
                    'RUNNING'
                )
                RETURNING run_id::text
                """
            ),
            {
                "run_id": run_uuid,
                "scenario_id": scenario_id,
                "projet_id": projet_id,
                "source_file": source_file,
                "source_type": source_type,
                "rows_in": rows_in,
            },
        ).one()
        return str(row[0])

    def complete_run(
        self,
        run_id: str,
        rows_out: int,
        rows_rejected: int,
        warnings: list[dict[str, Any]],
        errors: list[dict[str, Any]],
        duration_ms: int,
        status: str = "SUCCESS",
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE simulation_run
                SET
                    rows_out = :rows_out,
                    rows_rejected = :rows_rejected,
                    warnings_json = CAST(:warnings_json AS jsonb),
                    errors_json = CAST(:errors_json AS jsonb),
                    duration_ms = :duration_ms,
                    ended_at = :ended_at,
                    status = :status
                WHERE run_id = CAST(:run_id AS uuid)
                """
            ),
            {
                "run_id": run_id,
                "rows_out": rows_out,
                "rows_rejected": rows_rejected,
                "warnings_json": json.dumps(warnings),
                "errors_json": json.dumps(errors),
                "duration_ms": duration_ms,
                "ended_at": datetime.now(timezone.utc),
                "status": status,
            },
        )

    def save_warnings(self, run_id: str, warnings: list[dict[str, Any]]) -> None:
        self.db.execute(
            text("UPDATE simulation_run SET warnings_json = CAST(:payload AS jsonb) WHERE run_id = CAST(:run_id AS uuid)"),
            {"run_id": run_id, "payload": json.dumps(warnings)},
        )

    def save_errors(self, run_id: str, errors: list[dict[str, Any]]) -> None:
        self.db.execute(
            text("UPDATE simulation_run SET errors_json = CAST(:payload AS jsonb) WHERE run_id = CAST(:run_id AS uuid)"),
            {"run_id": run_id, "payload": json.dumps(errors)},
        )
