import io
from datetime import datetime, date
import json

try:
    import pandas as pd
except Exception:
    pd = None

from app.services.service_pipeline import ServicePipeline
from app.database import SessionLocal, engine
from sqlalchemy import text


def run_test():
    # Prepare audit_excel with datetime/date/pd.Timestamp
    audit_excel = {
        "fichier": "test.csv",
        "created_at": datetime(2026, 5, 30, 12, 34, 56),
        "metadata": {
            "date_only": date(2026, 5, 30),
            "nested_ts": pd.Timestamp("2026-05-30T13:00:00") if pd is not None else datetime(2026,5,30,13,0,0),
        },
    }

    # Monkeypatch ServiceAIMapping.extraire_lignes_normalisees used by ServicePipeline
    import app.services.service_pipeline as sp_mod

    def fake_extraire(self, contenu, nom_fichier):
        return [], audit_excel

    sp_mod.ServiceAIMapping.extraire_lignes_normalisees = fake_extraire

    # Create a minimal CSV bytes (ServiceAIMapping won't actually parse it because of monkeypatch)
    csv_bytes = b"designation;quantite;prix_total_ht\nItem A;1;100\n"

    # Run ServicePipeline.executer_depuis_excel directly with a DB session
    db = SessionLocal()
    try:
        sp = ServicePipeline(db)
        resultat = sp.executer_depuis_excel(csv_bytes, "test.csv")

        print("Result keys:", list(resultat.keys()))

        # Ensure response is JSON-serializable by dumping
        body = json.dumps(resultat)
        print("Serialized length:", len(body))

        # Check for date strings
        assert "2026-05-30T12:34:56" in body
        assert "2026-05-30T13:00:00" in body

        # Check DB counts
        with engine.connect() as conn:
            fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar()
            audit_count = conn.execute(text("SELECT COUNT(*) FROM dqe_import_audit")).scalar()

        print("fact_metre_count:", fact_count)
        print("dqe_import_audit_count:", audit_count)

        return 0
    except Exception as exc:
        print("ERROR", type(exc).__name__, exc)
        return 3
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = run_test()
    import sys
    sys.exit(exit_code)
