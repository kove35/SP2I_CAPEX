import sys
sys.path.insert(0, '07_API_BACKEND')
from app.services.service_simulation import ServiceSimulation
from app.schemas import SimulationRequest
from app.database import SessionLocal
from sqlalchemy import text

payload = {
    'items': [],
    'parameters': {
        'taux_landed_cost': {
            'transport_maritime': 0.12,
            'assurance': 0.02,
            'droits_douane': 0.15,
        },
        'seuil_decision_import': 0.97,
        'coefficient_risque': 1.1,
    },
    'mode': 'strict',
    'persist': False,
    'summary_only': False,
    'return_lines': True,
    'scenario_name': 'BASELINE',
    'scenario_type': 'IMPORT_OPTIMIZATION',
    'created_by': 'frontend',
}

db = SessionLocal()
service = ServiceSimulation(db=db)
result = service.simuler(SimulationRequest.model_validate(payload))
print('status', result['status'])
print('kpi', result['kpi'])
print('metadata', result['metadata'])
print('errors', result.get('errors'))
print('line_count', len(result['lignes']))
print('fact_metre_count', db.execute(text('SELECT COUNT(*) FROM fact_metre')).scalar_one())
print('trace', result.get('trace'))
db.close()
