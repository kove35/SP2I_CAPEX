from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text

from app.analytics.cache import analytics_cache
from app.analytics.utils.display_text import normalize_display_text
from app.database import SessionLocal


TABLES = {
    "fact_metre": ("id_ligne", ["lot", "designation", "famille", "batiment", "niveau", "decision_import"]),
    "dim_lot": ("lot_id", ["lot"]),
    "dim_batiment": ("batiment_id", ["batiment"]),
    "dim_niveau": ("niveau_id", ["niveau"]),
    "dim_famille": ("famille_id", ["famille", "libelle_famille"]),
}


def repair_display_encoding(dry_run: bool = True) -> dict:
    """
    Corrige les libelles deja stockes dans PostgreSQL.

    Usage typique en production Render :
    python 07_API_BACKEND/app/scripts/repair_display_encoding.py --yes
    """
    db = SessionLocal()
    report: dict[str, dict[str, int | str]] = {}
    total_repaired = 0
    try:
        for table_name, (pk_column, text_columns) in TABLES.items():
            try:
                rows = db.execute(
                    text(
                        f"""
                        SELECT {pk_column}, {", ".join(text_columns)}
                        FROM {table_name}
                        """
                    )
                ).mappings().all()
            except Exception as exc:
                report[table_name] = {"status": "SKIPPED", "reason": str(exc)}
                continue

            repaired = 0
            for row in rows:
                updates = {}
                for column in text_columns:
                    before = row.get(column)
                    after = normalize_display_text(before)
                    if after != before:
                        updates[column] = after

                if not updates:
                    continue

                repaired += 1
                if dry_run:
                    continue

                set_sql = ", ".join(f"{column} = :{column}" for column in updates)
                db.execute(
                    text(f"UPDATE {table_name} SET {set_sql} WHERE {pk_column} = :pk_value"),
                    {**updates, "pk_value": row[pk_column]},
                )

            total_repaired += repaired
            report[table_name] = {"status": "OK", "rows_repaired": repaired}

        if dry_run:
            db.rollback()
        else:
            db.commit()
            analytics_cache.clear()

        return {
            "status": "DRY_RUN" if dry_run else "SUCCESS",
            "total_rows_repaired": total_repaired,
            "tables": report,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Repare les libelles corrompus pour le frontend et Power BI.")
    parser.add_argument("--yes", action="store_true", help="Autorise les UPDATE PostgreSQL.")
    args = parser.parse_args()
    print(json.dumps(repair_display_encoding(dry_run=not args.yes), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
