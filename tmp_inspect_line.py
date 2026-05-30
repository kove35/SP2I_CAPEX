import csv
import json
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, '07_API_BACKEND')
from app.database import engine

key = 'LOT_SOL|OBJ_SOL_001'
print('--- POSTGRESQL fact_metre ---')
with engine.connect() as conn:
    row = conn.execute(text('SELECT id_ligne, designation, quantite, unite, prix_total_ht, capex_local, capex_import, decision_import, statut_ligne, source_file_type, date_import FROM fact_metre WHERE id_ligne = :id'), {'id': key}).fetchone()
    if not row:
        print('NOT FOUND')
    else:
        print('ROW=', dict(row._mapping))

base = Path('.')
files = [
    base / '06_ANALYSE_BI' / 'dataset' / 'FACT_METRE.csv',
    base / '05_RESULTATS' / 'optimisation_capex_import.csv',
    base / '03_DONNEES_ENTREE' / 'DQE' / 'dqe_normalise.json',
]
for path in files:
    print(f'--- SOURCE {path} ---')
    if not path.exists():
        print('MISSING')
        continue
    if path.suffix == '.csv':
        with path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f, delimiter=';')
            header = next(reader, None)
            found = False
            for r in reader:
                if r and (r[0] == key or 'OBJ_SOL_001' in r):
                    found = True
                    print('header=', header)
                    print('row=', r)
                    break
            if not found:
                print('NOT FOUND')
    elif path.suffix == '.json':
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

            def find_id(obj):
                if isinstance(obj, dict):
                    if obj.get('id_ligne') == 'OBJ_SOL_001':
                        return obj
                    for v in obj.values():
                        found = find_id(v)
                        if found is not None:
                            return found
                elif isinstance(obj, list):
                    for item in obj:
                        found = find_id(item)
                        if found is not None:
                            return found
                return None

            item = find_id(data)
            if item is not None:
                print(json.dumps(item, indent=2, ensure_ascii=False))
            else:
                print('NOT FOUND')
