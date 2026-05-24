from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def assert_equal(label: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> None:
    from app.models import SiteExecutionAction
    from app.services.site_execution_actions import (
        normalize_action_status,
        normalize_priority,
        summarize_execution_action_counts,
    )

    assert_equal("table name", SiteExecutionAction.__tablename__, "site_execution_actions")
    assert_equal("unknown status", normalize_action_status("started"), "TO_DO")
    assert_equal("done status", normalize_action_status("DONE"), "DONE")
    assert_equal("unknown priority", normalize_priority("urgent"), "MEDIUM")
    assert_equal("critical priority", normalize_priority("critical"), "CRITICAL")

    blocked = summarize_execution_action_counts({}, procurement_ready=False)
    assert_equal("blocked status", blocked["status"], "BLOCKED")

    required = summarize_execution_action_counts({"actions_count": 0}, procurement_ready=True)
    assert_equal("required status", required["status"], "REQUIRED")

    ready = summarize_execution_action_counts({
        "actions_count": 3,
        "open_count": 2,
        "blocked_count": 0,
        "at_risk_count": 0,
    })
    assert_equal("ready status", ready["status"], "READY")

    at_risk = summarize_execution_action_counts({
        "actions_count": 3,
        "open_count": 2,
        "blocked_count": 0,
        "at_risk_count": 1,
    })
    assert_equal("at risk status", at_risk["status"], "AT_RISK")

    active = summarize_execution_action_counts({
        "actions_count": 3,
        "open_count": 0,
        "blocked_count": 0,
        "at_risk_count": 0,
    })
    assert_equal("active status", active["status"], "ACTIVE")

    print("OK - site_execution_actions model and status helpers are valid.")


if __name__ == "__main__":
    main()
