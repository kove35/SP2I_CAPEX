from __future__ import annotations

from typing import Any

from app.governance.rules import row_has_blocking_loss


def is_data_loss(row: dict[str, Any]) -> bool:
    return row_has_blocking_loss(row)


def analytics_state(live: bool, stale: bool = False) -> str:
    if live:
        return "LIVE"
    return "STALE" if stale else "SNAPSHOT"
