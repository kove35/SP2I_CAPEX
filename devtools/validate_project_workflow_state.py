from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.workflow.project_workflow_state import WorkflowMetrics, compute_project_workflow_state_from_metrics


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> None:
    state = compute_project_workflow_state_from_metrics(
        WorkflowMetrics(
            setup_configured=True,
            fact_metre_rows=290,
            fact_metre_project_rows=290,
            capex_local_total=125_000_000,
            latest_trust_score=99,
            latest_file_name="SP2I_BIM_DQE_MASTER_V4_ENTERPRISE.xlsx",
            simulation_rows=290,
            simulation_project_rows=290,
            procurement_fact_decisions_count=290,
            execution_actions_count=0,
        )
    )
    assert_equal(state["dqe"], "SYNCHRONISE", "dqe")
    assert_equal(state["budget"], "SYNCHRONISE", "budget")
    assert_equal(state["scenarios"], "SIMULE", "scenarios")
    assert_equal(state["procurement"], "PRET", "procurement")
    assert_equal(state["execution"], "A_PREPARER", "execution")
    assert_equal(state["trust_score"], 99, "trust_score")
    assert_equal(state["progress_percent"], 83, "progress_percent")

    fallback_trust = compute_project_workflow_state_from_metrics(
        WorkflowMetrics(setup_configured=True, fact_metre_rows=1, capex_local_total=1)
    )
    assert_equal(fallback_trust["trust_score"], 99, "fallback trust_score")

    empty = compute_project_workflow_state_from_metrics(WorkflowMetrics())
    assert_equal(empty["dqe"], "A_IMPORTER", "empty dqe")
    assert_equal(empty["budget"], "A_SYNCHRONISER", "empty budget")

    print("[OK] Project workflow state centralise")
    print(state)


if __name__ == "__main__":
    main()
