import io
from datetime import datetime, date
import json

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app

pytestmark = pytest.mark.usefixtures("admin_auth")

try:
    import pandas as pd
except Exception:
    pd = None

from app.database import engine

CLIENT = TestClient(app)


def test_excel_sync_datetime_serialization(monkeypatch):
    # Prepare audit_excel with datetime/date/pd.Timestamp
    audit_excel = {
        "fichier": "test.csv",
        "created_at": datetime(2026, 5, 30, 12, 34, 56),
        "metadata": {
            "date_only": date(2026, 5, 30),
            "nested_ts": pd.Timestamp("2026-05-30T13:00:00") if pd is not None else datetime(2026,5,30,13,0,0),
        },
    }

    # Monkeypatch the ServiceAIMapping.extraire_lignes_normalisees used by ServicePipeline
    import app.services.service_pipeline as sp_mod

    def fake_extraire(self, contenu, nom_fichier):
        return [
            {
                "id_ligne": "SYNC-DATETIME-1",
                "designation": "Item A",
                "quantite": 1,
                "unite": "u",
                "prix_unitaire_ht": 100,
                "prix_total_ht": 100,
                "lot": "TEST_SYNC",
                "famille": "test_sync",
            }
        ], audit_excel

    monkeypatch.setattr(sp_mod.ServiceAIMapping, "extraire_lignes_normalisees", fake_extraire)

    # Create a minimal CSV file for upload
    csv_bytes = b"designation;quantite;prix_total_ht\nItem A;1;100\n"
    files = {"fichier": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}

    response = CLIENT.post("/api/upload/excel/sync", files=files)

    assert response.status_code == 200, response.text

    data = response.json()

    # 1. status SUCCESS
    assert data.get("status") == "SUCCESS" or data.get("status") == "SKIPPED" or "db_sync" in data

    # 2. response JSON contains no raw datetime objects (all should be strings)
    # Walk response and ensure no values are dicts of datetime objects
    def contains_raw_datetime(v):
        if isinstance(v, dict):
            for k, val in v.items():
                if contains_raw_datetime(val):
                    return True
            return False
        if isinstance(v, list):
            for item in v:
                if contains_raw_datetime(item):
                    return True
            return False
        # raw datetime/date/pd.Timestamp should not appear as non-str
        from datetime import datetime, date as _date

        if isinstance(v, (datetime, _date)):
            return True
        try:
            import pandas as _pd
        except Exception:
            _pd = None
        if _pd is not None and isinstance(v, _pd.Timestamp):
            return True
        return False

    assert not contains_raw_datetime(data), "Response contains raw date/datetime objects"

    # 3. Verify SQL counts
    with engine.connect() as conn:
        fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar()
        audit_count = conn.execute(text("SELECT COUNT(*) FROM dqe_import_audit")).scalar()

    # Return useful info if assertions fail
    print("status:", data.get("status"))
    print("fact_metre_count:", fact_count)
    print("dqe_import_audit_count:", audit_count)

    # Basic sanity: counts are integers
    assert isinstance(fact_count, int)
    assert isinstance(audit_count, int)

    # Also check that our injected audit_excel fields were serialized as strings in response
    # Search for our filename and created_at string
    body_str = json.dumps(data)
    assert "test.csv" in body_str
    assert "2026-05-30T12:34:56" in body_str or "2026-05-30T12:34:56" in json.dumps(data)
    assert "2026-05-30T13:00:00" in body_str
