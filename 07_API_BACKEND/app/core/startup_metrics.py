from __future__ import annotations

import time
from typing import Any

PROCESS_STARTED_AT = time.time()
STARTUP_TIMING: dict[str, Any] = {
    "process_started_at": PROCESS_STARTED_AT,
    "startup_complete": False,
    "startup_begin_at": None,
    "database_connect_ms": None,
    "schema_check_ms": None,
    "analytics_cache_load_ms": None,
    "startup_complete_at": None,
    "startup_ms": None,
}

COLD_START_WINDOW_SECONDS = 300


def record_startup_stage(stage: str, elapsed_ms: float) -> None:
    STARTUP_TIMING[f"{stage}_ms"] = round(elapsed_ms, 2)


def mark_startup_begin() -> None:
    STARTUP_TIMING["startup_begin_at"] = time.time()


def mark_startup_complete() -> None:
    STARTUP_TIMING["startup_complete"] = True
    STARTUP_TIMING["startup_complete_at"] = time.time()
    STARTUP_TIMING["startup_ms"] = round(
        (STARTUP_TIMING["startup_complete_at"] - STARTUP_TIMING["startup_begin_at"]) * 1000,
        2,
    )


def get_startup_status() -> dict[str, Any]:
    now = time.time()
    uptime_seconds = round(now - PROCESS_STARTED_AT, 2)
    startup_ms = STARTUP_TIMING.get("startup_ms")
    return {
        "process_started_at": STARTUP_TIMING["process_started_at"],
        "uptime_seconds": uptime_seconds,
        "startup_begin_at": STARTUP_TIMING.get("startup_begin_at"),
        "database_connect_ms": STARTUP_TIMING.get("database_connect_ms"),
        "schema_check_ms": STARTUP_TIMING.get("schema_check_ms"),
        "analytics_cache_load_ms": STARTUP_TIMING.get("analytics_cache_load_ms"),
        "startup_complete_at": STARTUP_TIMING.get("startup_complete_at"),
        "startup_ms": startup_ms,
        "is_cold_start": uptime_seconds <= COLD_START_WINDOW_SECONDS,
        "startup_complete": STARTUP_TIMING.get("startup_complete", False),
        "cold_start_window_seconds": COLD_START_WINDOW_SECONDS,
    }
