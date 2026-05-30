import sys
from pathlib import Path
sys.path.insert(0, '07_API_BACKEND')
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM fact_metre LIMIT 1'))
    print('COLUMNS=', result.keys())
    row = result.fetchone()
    if row is not None:
        print('ROW=', dict(zip(result.keys(), row)))
    else:
        print('ROW= None')

    print('\n--- SINGLE ROW FOR LOT_SOL|OBJ_SOL_001 ---')
    row2 = conn.execute(text('SELECT * FROM fact_metre WHERE id_ligne = :id'), {'id': 'LOT_SOL|OBJ_SOL_001'}).fetchone()
    if row2 is not None:
        print('ROW2=', dict(zip(result.keys(), row2)))
    else:
        print('ROW2= NOT FOUND')
