"""Prepare la base isolee dediee a test_excel_sync_datetime_serialization.

Le test exerce une VRAIE synchronisation (ServicePipeline -> PostgreSQL). Il
echoue au runtime sur la base minimale car il manque les tables du schema metier
complet (dim_lot, dim_niveau, fact_simulation, dqe_import_audit, colonnes
analytiques de fact_metre...).

Cette preparation applique les DEFINITIONS DU DEPOT :
  1. Base.metadata.create_all (tables ORM) ;
  2. le grand SQL de cloud_migrations.ensure_powerbi_schema (extrait tel quel,
     sans la partie ANALYTICS_VIEWS_SQL qui exige la chaine de migrations
     complete). Le test n'est ni desactive ni simule.

Usage (depuis 07_API_BACKEND) :
    python tests/recette/prepare_sync_db.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

DB = "sp2i_capex_sync_test"
os.environ["DATABASE_URL"] = f"postgresql://user:password@localhost:5433/{DB}"
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_STARTUP_SCHEMA_MUTATIONS"] = "false"
os.environ["SP2I_JWT_SECRET"] = "recette-local-secret-change-before-production-0123456789"

import subprocess  # noqa: E402


def _extract_powerbi_ddl() -> str:
    """Extrait le grand SQL idempotent de ensure_powerbi_schema (definitions du depot)."""
    src_path = Path(__file__).resolve().parents[2] / "app" / "cloud_migrations.py"
    src = src_path.read_text(encoding="utf-8")
    marker = 'sql = """'
    start = src.index(marker) + len(marker)
    end = src.index('"""', start)
    return src[start:end].strip("\n")


def main() -> int:
    subprocess.run(
        ["docker", "exec", "sp2i_capex_test_pg", "psql", "-U", "user", "-d", "postgres",
         "-c", f"DROP DATABASE IF EXISTS {DB};", "-c", f"CREATE DATABASE {DB};"],
        check=True, capture_output=True,
    )
    print("db created:", DB)

    from app.database import Base, engine  # noqa: E402
    from app.main import app as _app  # noqa: F401,E402

    Base.metadata.create_all(bind=engine)
    print("create_all done")

    ddl = _extract_powerbi_ddl()
    with engine.begin() as conn:
        conn.exec_driver_sql(ddl)
    print("powerbi DDL applied (tables + colonnes analytiques)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
