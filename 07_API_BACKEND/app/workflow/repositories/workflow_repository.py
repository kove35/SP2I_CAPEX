from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.projects.models import Project
from app.services.procurement_decisions import procurement_decision_status
from app.workflow.project_workflow_state import collect_project_workflow_metrics


class WorkflowRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_project(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def collect_snapshot(self, project_id: int, setup_status: str | None = None) -> dict[str, Any]:
        project = self.get_project(project_id)
        setup = setup_status if setup_status is not None else getattr(project, "setup_status", None)
        base_metrics = collect_project_workflow_metrics(self.db, project_id, setup_configured=str(setup or "").upper() in {"CONFIGURED", "ACTIVE", "DONE"})
        procurement = procurement_decision_status(self.db, project_id, scenario_ready=base_metrics.simulation_rows > 0) or {}
        return {
            "project": project,
            "setup_status": setup,
            "base_metrics": base_metrics,
            "procurement": procurement,
            "execution": self._execution_counts(project_id),
            "orders_count": self._safe_count("procurement_orders", project_id),
            "containers_count": self._safe_count("logistics_containers", project_id),
            "received_count": self._safe_count("logistics_receipts", project_id),
            "eta_average_days": self._safe_avg_eta(project_id),
            "supplier_unconfirmed_count": self._safe_supplier_unconfirmed(project_id),
        }

    def _safe_count(self, table_name: str, project_id: int) -> int:
        if table_name not in {"procurement_orders", "logistics_containers", "logistics_receipts"}:
            return 0
        try:
            return int(self.db.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE project_id = :project_id"), {"project_id": project_id}).scalar_one_or_none() or 0)
        except Exception:
            return 0

    def _safe_avg_eta(self, project_id: int) -> int:
        try:
            value = self.db.execute(
                text("SELECT AVG(eta_days) FROM logistics_containers WHERE project_id = :project_id"),
                {"project_id": project_id},
            ).scalar_one_or_none()
            return int(value or 0)
        except Exception:
            return 0

    def _safe_supplier_unconfirmed(self, project_id: int) -> int:
        try:
            return int(
                self.db.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM procurement_decisions
                        WHERE project_id = :project_id
                          AND COALESCE(supplier_selected, '') = ''
                        """
                    ),
                    {"project_id": project_id},
                ).scalar_one_or_none()
                or 0
            )
        except Exception:
            return 0

    def _execution_counts(self, project_id: int) -> dict[str, int]:
        try:
            row = self.db.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS actions_count,
                        COUNT(*) FILTER (WHERE status = 'DONE') AS done_count,
                        COUNT(*) FILTER (WHERE status = 'BLOCKED') AS blocked_count,
                        COUNT(*) FILTER (WHERE status = 'AT_RISK') AS at_risk_count
                    FROM site_execution_actions
                    WHERE project_id = :project_id
                    """
                ),
                {"project_id": project_id},
            ).mappings().first()
        except Exception:
            row = None
        return {key: int((row or {}).get(key) or 0) for key in ("actions_count", "done_count", "blocked_count", "at_risk_count")}
