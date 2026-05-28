from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.workflow.engine.workflow_metrics import compute_workflow_metrics
from app.workflow.engine.workflow_readiness import compute_readiness
from app.workflow.engine.workflow_rules import (
    compute_active_step,
    compute_alerts,
    compute_blockers,
    compute_next_action,
    compute_workflow_state,
)
from app.workflow.engine.workflow_timeline import compute_timeline
from app.workflow.engine.workflow_transitions import allowed_next_states
from app.workflow.repositories.workflow_repository import WorkflowRepository
from app.workflow.schemas.workflow import WorkflowState
from app.workflow.services.workflow_cache import workflow_cache


class WorkflowStateEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = WorkflowRepository(db)

    def compute(self, project_id: int, setup_status: str | None = None, use_cache: bool = True) -> WorkflowState:
        if use_cache:
            cached = workflow_cache.get(project_id)
            if cached:
                return WorkflowState(**cached)

        snapshot = self.repository.collect_snapshot(project_id, setup_status=setup_status)
        workflow_state = compute_workflow_state(snapshot)
        metrics = compute_workflow_metrics(snapshot, workflow_state)
        blockers = compute_blockers(workflow_state, snapshot, metrics)
        alerts = compute_alerts(workflow_state, metrics, blockers)
        state = WorkflowState(
            project_id=project_id,
            workflow_state=workflow_state,
            active_step=compute_active_step(workflow_state),
            next_action=compute_next_action(workflow_state, metrics),
            progress_percent=metrics.progress_percent,
            procurement_state=self._procurement_state(workflow_state),
            approval_state=self._approval_state(workflow_state, metrics),
            logistics_state=self._logistics_state(workflow_state),
            execution_state=self._execution_state(workflow_state, metrics),
            readiness=compute_readiness(workflow_state, metrics),
            blockers=blockers,
            alerts=alerts,
            timeline=compute_timeline(workflow_state, metrics, blockers),
            metrics=metrics,
            transitions=allowed_next_states(workflow_state),
            **self._legacy_fields(snapshot, workflow_state, metrics),
        )
        workflow_cache.set(project_id, state.model_dump(mode="json"))
        return state

    def recompute_project_workflow(self, project_id: int, setup_status: str | None = None) -> dict[str, Any]:
        return self.compute(project_id, setup_status=setup_status, use_cache=False).model_dump(mode="json")

    def recompute_after_procurement_validation(
        self,
        project_id: int,
        scenario_id: str | None = None,
        setup_status: str | None = None,
        scenario_ready: bool = True,
    ) -> dict[str, Any]:
        del scenario_id, scenario_ready
        snapshot = self.repository.collect_snapshot(project_id, setup_status=setup_status)
        return {
            "workflow": self.recompute_project_workflow(project_id, setup_status=setup_status),
            "procurement": snapshot.get("procurement") or {},
        }

    def invalidate(self, project_id: int | None = None) -> None:
        workflow_cache.invalidate(project_id)

    @staticmethod
    def _procurement_state(workflow_state: str) -> str:
        if workflow_state in {"CONFIGURATION", "DQE_CERTIFIED", "BUDGET_SYNCED", "SIMULATION_READY"}:
            return "BLOCKED"
        if workflow_state in {"SIMULATION_COMPLETED", "ARBITRAGE_IN_PROGRESS"}:
            return "IN_PROGRESS"
        if workflow_state in {"ARBITRAGE_COMPLETED", "PROCUREMENT_VALIDATED", "ORDER_READY", "ORDERED", "IN_TRANSIT", "RECEIVED", "CHANTIER_READY", "EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"}:
            return "VALIDATED"
        return "BLOCKED"

    @staticmethod
    def _approval_state(workflow_state: str, metrics) -> str:
        if workflow_state == "ARBITRAGE_IN_PROGRESS" and metrics.pending_lines:
            return "REQUIRED"
        if workflow_state in {"ARBITRAGE_COMPLETED", "PROCUREMENT_VALIDATED", "ORDER_READY", "ORDERED", "IN_TRANSIT", "RECEIVED", "CHANTIER_READY", "EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"}:
            return "APPROVED"
        return "NOT_REQUIRED"

    @staticmethod
    def _logistics_state(workflow_state: str) -> str:
        if workflow_state in {"ORDERED", "IN_TRANSIT"}:
            return "ACTIVE"
        if workflow_state in {"RECEIVED", "CHANTIER_READY", "EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"}:
            return "RECEIVED"
        return "BLOCKED"

    @staticmethod
    def _execution_state(workflow_state: str, metrics) -> str:
        if metrics.execution_blocked or metrics.execution_at_risk:
            return "AT_RISK"
        if workflow_state in {"EXECUTION_IN_PROGRESS"}:
            return "ACTIVE"
        if workflow_state == "EXECUTION_COMPLETED":
            return "COMPLETED"
        if workflow_state == "CHANTIER_READY":
            return "READY"
        return "BLOCKED"

    @staticmethod
    def _legacy_fields(snapshot: dict[str, Any], workflow_state: str, metrics) -> dict[str, Any]:
        base = snapshot.get("base_metrics")
        setup = "CONFIGURE" if getattr(base, "setup_configured", False) else "A_COMPLETER"
        dqe = "SYNCHRONISE" if metrics.dqe_lines > 0 else "A_IMPORTER"
        budget = "SYNCHRONISE" if metrics.capex_local_total > 0 else "A_SYNCHRONISER"
        scenarios = "SIMULE" if metrics.simulation_lines > 0 else "A_SIMULER"
        procurement = "PRET" if workflow_state not in {"CONFIGURATION", "DQE_CERTIFIED", "BUDGET_SYNCED", "SIMULATION_READY", "SIMULATION_COMPLETED", "ARBITRAGE_IN_PROGRESS"} else ("A_PREPARER" if metrics.simulation_lines else "BLOQUE")
        execution = "PRETE" if workflow_state in {"CHANTIER_READY", "EXECUTION_IN_PROGRESS", "EXECUTION_COMPLETED"} else ("A_PREPARER" if procurement == "PRET" else "BLOQUEE")
        return {
            "setup": setup,
            "dqe": dqe,
            "budget": budget,
            "scenarios": scenarios,
            "procurement": procurement,
            "execution": execution,
            "trust_score": int(getattr(base, "latest_trust_score", 0) or (99 if metrics.dqe_lines else 0)),
            "normalized_lines_count": int(metrics.dqe_lines or getattr(base, "latest_fact_rows", 0) or getattr(base, "latest_audit_rows", 0) or 0),
            "capex_local_total": round(metrics.capex_local_total, 2),
            "counts": {
                "fact_metre_rows": int(getattr(base, "fact_metre_rows", 0) or 0),
                "fact_metre_project_rows": int(getattr(base, "fact_metre_project_rows", 0) or 0),
                "simulation_rows": int(getattr(base, "simulation_rows", 0) or 0),
                "simulation_project_rows": int(getattr(base, "simulation_project_rows", 0) or 0),
                "procurement_decisions_count": int((snapshot.get("procurement") or {}).get("decisions_count") or 0),
                "procurement_validated_decisions_count": metrics.validated_lines,
                "execution_actions_count": metrics.execution_actions,
            },
            "file_name": str(getattr(base, "latest_file_name", "") or ""),
        }
