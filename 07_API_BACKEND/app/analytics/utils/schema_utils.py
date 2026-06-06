from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from sqlalchemy import text


logger = logging.getLogger("sp2i-capex-api.analytics.schema")

OPTIONAL_FACT_METRE_COLUMNS = (
    "appartement_id",
    "appartement_code",
    "appart",
    "appart_id",
    "piece",
    "piece_id",
    "piece_code",
    "piece_type",
    "type_zone",
    "ifc_guid",
    "ifc_type",
    "bim_object",
    "bim_object_id",
    "omniclass",
    "uniclass",
    "classification",
    "type_objet",
    "famille_bim",
    "systeme",
    "phase_chantier",
)

_COLUMN_CACHE: dict[str, set[str]] = {}
_WARNING_CACHE: set[tuple[str, str]] = set()


def cache_key(table_name: str, schema_name: str | None = None) -> str:
    schema = schema_name or "current_schema()"
    return f"{schema}.{table_name}".lower()


def clear_schema_cache() -> None:
    _COLUMN_CACHE.clear()
    _WARNING_CACHE.clear()


def load_table_columns(db: Any, table_name: str, schema_name: str | None = None, force: bool = False) -> set[str]:
    key = cache_key(table_name, schema_name)
    if not force and key in _COLUMN_CACHE:
        return _COLUMN_CACHE[key]

    if schema_name:
        where_schema = "table_schema = :schema_name"
        params = {"table_name": table_name, "schema_name": schema_name}
    else:
        where_schema = "table_schema = current_schema()"
        params = {"table_name": table_name}

    rows = db.execute(
        text(
            f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE {where_schema}
              AND table_name = :table_name
            """
        ),
        params,
    ).scalars().all()
    columns = {str(column) for column in rows}
    _COLUMN_CACHE[key] = columns
    return columns


def preload_schema_capabilities(db: Any, tables: Iterable[str] = ("fact_metre",)) -> dict[str, dict[str, bool]]:
    return {
        table_name: schema_capabilities(db, table_name, force=True)
        for table_name in tables
    }


def column_exists(db: Any, table_name: str, column_name: str) -> bool:
    return column_name in load_table_columns(db, table_name)


def schema_capabilities(
    db: Any,
    table_name: str = "fact_metre",
    columns: Iterable[str] = OPTIONAL_FACT_METRE_COLUMNS,
    force: bool = False,
) -> dict[str, bool]:
    available = load_table_columns(db, table_name, force=force)
    return {column: column in available for column in columns}


def warn_missing_column(table_name: str, column_name: str) -> None:
    key = (table_name, column_name)
    if key in _WARNING_CACHE:
        return
    _WARNING_CACHE.add(key)
    logger.warning("Optional column missing: %s.%s", table_name, column_name)


def optional_column_sql(columns: set[str], column_name: str, alias: str | None = None, default_sql: str = "NULL") -> str:
    if column_name in columns:
        expression = column_name
    else:
        warn_missing_column("fact_metre", column_name)
        expression = default_sql
    return f"{expression} AS {alias}" if alias else expression


def first_non_empty_sql(columns: set[str], candidates: Iterable[str], default_sql: str = "NULL") -> str:
    available: list[str] = []
    for column in candidates:
        if column in columns:
            available.append(f"NULLIF(TRIM(CAST({column} AS text)), '')")
        else:
            warn_missing_column("fact_metre", column)
    if not available:
        return default_sql
    return f"COALESCE({', '.join(available)})"
