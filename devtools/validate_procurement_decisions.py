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
    from app.models import ProcurementDecision
    from app.services.procurement_decisions import (
        normalize_decision,
        normalize_validation_status,
        summarize_procurement_decision_counts,
    )

    assert_equal("table name", ProcurementDecision.__tablename__, "procurement_decisions")
    assert_equal("hybrid decision", normalize_decision("MIXTE"), "HYBRID")
    assert_equal("unknown decision", normalize_decision(""), "REVIEW_REQUIRED")
    assert_equal("unknown status", normalize_validation_status("done"), "PENDING")

    blocked = summarize_procurement_decision_counts({}, scenario_ready=False)
    assert_equal("blocked status", blocked["status"], "BLOCKED")

    required = summarize_procurement_decision_counts({"decisions_count": 0})
    assert_equal("required status", required["status"], "REQUIRED")

    review = summarize_procurement_decision_counts({
        "decisions_count": 3,
        "pending_decisions_count": 3,
        "validated_decisions_count": 0,
    })
    assert_equal("review status", review["status"], "REVIEW_REQUIRED")

    ready = summarize_procurement_decision_counts({
        "decisions_count": 3,
        "validated_decisions_count": 2,
        "critical_pending_count": 0,
        "blocked_decisions_count": 0,
    })
    assert_equal("ready status", ready["status"], "READY")

    print("OK - procurement_decisions model and status helpers are valid.")


if __name__ == "__main__":
    main()
