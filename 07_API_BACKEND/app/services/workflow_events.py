from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def _safe_metadata(metadata: dict[str, Any] | None = None) -> str:
    try:
        return json.dumps(metadata or {}, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return "{}"


def log_workflow_event(
    db: Session,
    *,
    project_id: int,
    user_id: int | None = None,
    event_type: str,
    entity_type: str = "",
    entity_id: str | int | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
    message: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    try:
        db.execute(
            text(
                """
                INSERT INTO workflow_events (
                    project_id,
                    user_id,
                    event_type,
                    entity_type,
                    entity_id,
                    previous_status,
                    new_status,
                    message,
                    metadata_json,
                    created_at
                )
                VALUES (
                    :project_id,
                    :user_id,
                    :event_type,
                    :entity_type,
                    :entity_id,
                    :previous_status,
                    :new_status,
                    :message,
                    :metadata_json,
                    now()
                )
                """
            ),
            {
                "project_id": project_id,
                "user_id": user_id,
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": str(entity_id or ""),
                "previous_status": previous_status or "",
                "new_status": new_status or "",
                "message": message,
                "metadata_json": _safe_metadata(metadata),
            },
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()


def list_workflow_events(
    db: Session,
    project_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                id,
                project_id,
                user_id,
                event_type,
                entity_type,
                entity_id,
                previous_status,
                new_status,
                message,
                metadata_json,
                created_at
            FROM workflow_events
            WHERE project_id = :project_id
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"project_id": project_id, "limit": limit, "offset": offset},
    ).mappings().all()
    events: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        except (TypeError, ValueError):
            item["metadata"] = {}
        events.append(item)
    return events
