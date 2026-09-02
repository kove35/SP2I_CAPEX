from __future__ import annotations

import json
import sys
from collections.abc import Iterable

from sqlalchemy import inspect, text

from app.database import engine


REQUIRED_COLUMNS: dict[str, set[str]] = {
    "users": {"id", "email", "password_hash", "role", "is_active"},
    "projects": {"id", "owner_id", "name", "status"},
    "workspace_memberships": {"user_id", "project_id", "role"},
    "dim_projet": {"projet_id", "projet_code"},
    "fact_metre": {"projet_id"},
}


def _missing(expected: Iterable[str], actual: Iterable[str]) -> list[str]:
    return sorted(set(expected) - set(actual))


def run_checks() -> dict[str, object]:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names(schema="public"))
    missing_tables = _missing(REQUIRED_COLUMNS, tables)
    missing_columns: dict[str, list[str]] = {}
    for table, expected in REQUIRED_COLUMNS.items():
        if table not in tables:
            continue
        actual = {column["name"] for column in inspector.get_columns(table, schema="public")}
        absent = _missing(expected, actual)
        if absent:
            missing_columns[table] = absent

    active_admins = 0
    project_links_without_access = 0
    fact_rows_without_project = 0
    if not missing_tables and not missing_columns:
        with engine.connect() as connection:
            active_admins = int(
                connection.execute(
                    text("SELECT COUNT(*) FROM users WHERE UPPER(role) = 'ADMIN' AND is_active IS TRUE")
                ).scalar_one()
            )
            project_links_without_access = int(
                connection.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM dim_projet dp
                        LEFT JOIN projects p ON p.id = dp.projet_id
                        WHERE p.id IS NULL
                        """
                    )
                ).scalar_one()
            )
            fact_rows_without_project = int(
                connection.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM fact_metre f
                        LEFT JOIN dim_projet dp ON dp.projet_id = f.projet_id
                        WHERE f.projet_id IS NULL OR dp.projet_id IS NULL
                        """
                    )
                ).scalar_one()
            )

    blockers: list[str] = []
    if missing_tables:
        blockers.append("missing_tables")
    if missing_columns:
        blockers.append("missing_columns")
    if active_admins < 1:
        blockers.append("no_active_admin")
    if project_links_without_access:
        blockers.append("unlinked_project_scope")
    if fact_rows_without_project:
        blockers.append("unscoped_fact_rows")

    return {
        "status": "READY" if not blockers else "BLOCKED",
        "blockers": blockers,
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "active_admins": active_admins,
        "project_links_without_access": project_links_without_access,
        "fact_rows_without_project": fact_rows_without_project,
    }


def main() -> int:
    try:
        result = run_checks()
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error_type": type(exc).__name__}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    sys.exit(main())
