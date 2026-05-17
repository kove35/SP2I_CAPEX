from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text

from app.analytics.cache import analytics_cache
from app.analytics.repositories import AnalyticsRepository
from app.cloud_migrations import ensure_powerbi_schema
from app.database import Base, SessionLocal, engine
from app.services.service_pipeline import ServicePipeline


DATASET_PATH = PROJECT_ROOT / "03_DONNEES_REFERENCE" / "SP2I_CAPEX_DEMO_V1.xlsx"
METADATA_PATH = PROJECT_ROOT / "03_DONNEES_REFERENCE" / "DATASET_METADATA.json"


def _load_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def _print_ok(message: str) -> None:
    print(f"[OK] {message}")


def _print_warn(message: str) -> None:
    print(f"[WARN] {message}")


def _validate_database(db) -> dict:
    repo = AnalyticsRepository(db)
    kpis = repo.kpis(query=_empty_query())
    lots = db.execute(text("SELECT COUNT(DISTINCT lot) FROM fact_metre")).scalar_one()
    import_count = db.execute(text("SELECT COUNT(*) FROM fact_metre WHERE decision_import = 'IMPORT'")).scalar_one()
    return {
        "nb_lignes": int(kpis.get("nb_lignes") or 0),
        "nb_lots": int(lots or 0),
        "capex_brut": round(float(kpis.get("capex_brut") or 0), 2),
        "capex_optimise": round(float(kpis.get("capex_optimise") or 0), 2),
        "economie_nette": round(float(kpis.get("economie_nette") or 0), 2),
        "nb_import": int(import_count or 0),
    }


def _empty_query():
    from app.analytics.schemas import AnalyticsQuery

    return AnalyticsQuery()


def seed_database(dry_run: bool = True) -> dict:
    """
    Recharge le dataset officiel SP2I dans PostgreSQL.

    Le script est idempotent : le pipeline remplace `fact_metre` courant avant
    insertion, reconstruit les dimensions utiles et vide le cache analytics.
    Par securite, l'ecriture reelle demande `--yes`.
    """
    start = perf_counter()
    metadata = _load_metadata()

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset introuvable: {DATASET_PATH}")

    _print_ok(f"Dataset trouve: {DATASET_PATH.name}")
    if metadata:
        _print_ok(f"Metadata: {metadata.get('dataset')} v{metadata.get('version')}")

    if dry_run:
        _print_warn("Mode dry-run actif : aucune ecriture PostgreSQL.")
        return {
            "status": "DRY_RUN",
            "dataset": str(DATASET_PATH),
            "metadata": metadata,
        }

    Base.metadata.create_all(bind=engine)
    ensure_powerbi_schema(engine)
    _print_ok("Schema PostgreSQL verifie")

    db = SessionLocal()
    try:
        analytics_cache.clear()
        _print_ok("Cache analytics nettoye")

        result = ServicePipeline(db).executer_depuis_excel(DATASET_PATH.read_bytes(), DATASET_PATH.name)
        if result.get("status") != "SUCCESS":
            raise RuntimeError(f"Pipeline seed en erreur: {result}")

        db_sync = result.get("db_sync", {})
        if db_sync.get("status") != "SUCCESS":
            raise RuntimeError(f"Synchronisation PostgreSQL en erreur: {db_sync}")

        validation = _validate_database(db)
        expected_rows = int(metadata.get("nb_lignes") or 584)
        expected_capex = float(metadata.get("capex_total") or 1129667152)

        if validation["nb_lignes"] != expected_rows:
            raise RuntimeError(f"Nombre lignes inattendu: {validation['nb_lignes']} au lieu de {expected_rows}")
        if round(validation["capex_brut"]) != round(expected_capex):
            raise RuntimeError(f"CAPEX inattendu: {validation['capex_brut']} au lieu de {expected_capex}")
        if validation["nb_lots"] != int(metadata.get("nb_lots") or 14):
            raise RuntimeError(f"Nombre lots inattendu: {validation['nb_lots']}")

        _print_ok(f"{validation['nb_lignes']} lignes FACT_METRE")
        _print_ok(f"{validation['nb_lots']} lots detectes")
        _print_ok(f"CAPEX : {validation['capex_brut']:,.0f}".replace(",", " "))
        _print_ok(f"Economie : {validation['economie_nette']:,.0f}".replace(",", " "))
        _print_ok("Analytics views rebuilt")
        _print_ok("Seed completed")

        return {
            "status": "SUCCESS",
            "dataset": metadata.get("dataset", DATASET_PATH.name),
            "validation": validation,
            "db_sync": db_sync,
            "duration_ms": round((perf_counter() - start) * 1000, 2),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed PostgreSQL avec le dataset officiel SP2I CAPEX.")
    parser.add_argument("--yes", action="store_true", help="Autorise l'ecriture PostgreSQL.")
    args = parser.parse_args()
    result = seed_database(dry_run=not args.yes)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
