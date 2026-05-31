from app.database import SessionLocal
from app.utils.json_safe import sanitize_for_json

from app.analytics.schemas import AnalyticsQuery
from app.analytics.services.analytics_service import AnalyticsService
from app.workflow.engine.workflow_state_engine import WorkflowStateEngine
from app.projects.models import Project


def main():
    db = SessionLocal()
    try:
        # Analytics kpis
        print('Running AnalyticsService.kpis...')
        analytics = AnalyticsService(db).kpis(AnalyticsQuery())
        body = sanitize_for_json(analytics)
        import json as _json

        print('Analytics serialized length:', len(_json.dumps(body)))

        # Workflow state for first project
        project = db.query(Project).first()
        if not project:
            print('No project found; skipping workflow check')
            return

        print('Found project id', project.id)
        state = WorkflowStateEngine(db).compute(project.id, setup_status=project.setup_status)
        state_obj = sanitize_for_json(state.model_dump(mode='json') if hasattr(state, 'model_dump') else state)
        print('Workflow serialized length:', len(_json.dumps(state_obj)))
    finally:
        db.close()


if __name__ == '__main__':
    main()
