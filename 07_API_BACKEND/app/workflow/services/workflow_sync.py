from __future__ import annotations

from sqlalchemy.orm import Session

from app.workflow.engine.workflow_transitions import transition_for_event
from app.workflow.engine.workflow_state_engine import WorkflowStateEngine
from app.workflow.services.workflow_cache import workflow_cache
from app.workflow.services.workflow_events import log_workflow_event


class WorkflowSyncService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.engine = WorkflowStateEngine(db)

    def handle_event(
        self,
        *,
        project_id: int,
        event_type: str,
        user_id: int | None = None,
        entity_type: str = "",
        entity_id: str | int | None = None,
        reason: str = "",
        metadata: dict | None = None,
    ):
        previous_state = self.engine.compute(project_id, use_cache=False).workflow_state
        workflow_cache.invalidate(project_id)
        state = self.engine.compute(project_id, use_cache=False)
        target_state = transition_for_event(event_type) or state.workflow_state
        log_workflow_event(
            self.db,
            project_id=project_id,
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            previous_status=previous_state,
            new_status=target_state,
            message=reason,
            metadata={**(metadata or {}), "workflow_state": state.model_dump(mode="json")},
        )
        workflow_cache.invalidate(project_id)
        return state
