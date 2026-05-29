from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.workflow.engine.workflow_state_engine import WorkflowStateEngine
from app.workflow.project_workflow_state import WorkflowMetrics


class WorkflowSyncValidationTests(unittest.TestCase):
    def test_workflow_engine_marks_stale_fact_metre_out_of_sync(self):
        stale_metrics = WorkflowMetrics(
            setup_configured=True,
            fact_metre_rows=89,
            fact_metre_project_rows=89,
            capex_local_total=186235965.56,
            latest_trust_score=0,
            latest_file_name="",
            latest_audit_rows=0,
            latest_fact_rows=0,
            simulation_rows=0,
            simulation_project_rows=0,
            procurement_decisions_count=0,
            procurement_fact_decisions_count=0,
            execution_actions_count=0,
            execution_blocked_count=0,
            execution_at_risk_count=0,
            last_dqe_certification=None,
            last_fact_metre_sync=None,
            sync_status="OUT_OF_SYNC",
            sync_delta_rows=89,
            sync_delta_capex=186235965.56,
        )

        snapshot = {
            "project": None,
            "setup_status": "CONFIGURED",
            "base_metrics": stale_metrics,
            "procurement": {},
            "execution": {
                "actions_count": 0,
                "done_count": 0,
                "blocked_count": 0,
                "at_risk_count": 0,
            },
            "orders_count": 0,
            "containers_count": 0,
            "received_count": 0,
            "eta_average_days": 0,
            "supplier_unconfirmed_count": 0,
        }

        engine = WorkflowStateEngine(db=None)

        with patch.object(engine.repository, "collect_snapshot", return_value=snapshot):
            state = engine.compute(project_id=1, setup_status="CONFIGURED", use_cache=False)

        self.assertEqual("OUT_OF_SYNC", state.workflow_state)
        self.assertFalse(state.dqe_synced)
        self.assertEqual("OUT_OF_SYNC", state.sync_status)
        self.assertEqual(89, state.sync_delta_rows)
        self.assertEqual(186235965.56, state.sync_delta_capex)
        self.assertEqual("Resynchroniser le DQE", state.next_action.label)

    def test_workflow_engine_marks_matching_sync_as_synced(self):
        synced_metrics = WorkflowMetrics(
            setup_configured=True,
            fact_metre_rows=290,
            fact_metre_project_rows=290,
            capex_local_total=113928000.0,
            latest_trust_score=98,
            latest_file_name="dqe_source_brut.json",
            latest_audit_rows=290,
            latest_fact_rows=290,
            simulation_rows=0,
            simulation_project_rows=0,
            procurement_decisions_count=0,
            procurement_fact_decisions_count=0,
            execution_actions_count=0,
            execution_blocked_count=0,
            execution_at_risk_count=0,
            last_dqe_certification=datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc),
            last_fact_metre_sync=datetime(2026, 5, 29, 12, 5, tzinfo=timezone.utc),
            sync_status="SYNCED",
            sync_delta_rows=0,
            sync_delta_capex=0.0,
        )

        snapshot = {
            "project": None,
            "setup_status": "CONFIGURED",
            "base_metrics": synced_metrics,
            "procurement": {},
            "execution": {
                "actions_count": 0,
                "done_count": 0,
                "blocked_count": 0,
                "at_risk_count": 0,
            },
            "orders_count": 0,
            "containers_count": 0,
            "received_count": 0,
            "eta_average_days": 0,
            "supplier_unconfirmed_count": 0,
        }

        engine = WorkflowStateEngine(db=None)

        with patch.object(engine.repository, "collect_snapshot", return_value=snapshot):
            state = engine.compute(project_id=1, setup_status="CONFIGURED", use_cache=False)

        self.assertNotEqual("OUT_OF_SYNC", state.workflow_state)
        self.assertTrue(state.dqe_synced)
        self.assertEqual("SYNCED", state.sync_status)
        self.assertEqual(0, state.sync_delta_rows)
        self.assertEqual(0.0, state.sync_delta_capex)


if __name__ == "__main__":
    unittest.main()
