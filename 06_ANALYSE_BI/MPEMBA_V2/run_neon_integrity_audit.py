from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "07_API_BACKEND"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import DATABASE_URL_OBJ, database_url_database, database_url_host, database_url_is_neon, masked_database_url  # noqa: E402


OUT_DIR = Path(__file__).resolve().parent
JSON_OUT = OUT_DIR / "neon_integrity_audit_result.json"
MD_OUT = OUT_DIR / "neon_integrity_audit_report.md"


def rows(db: Any, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [dict(row) for row in db.execute(text(sql), params or {}).mappings().all()]


def scalar(db: Any, sql: str, params: dict[str, Any] | None = None) -> Any:
    return db.execute(text(sql), params or {}).scalar()


def exists_relation(db: Any, relation_name: str, kind: str = "r") -> bool:
    relkind = {"table": "r", "view": "v"}.get(kind, kind)
    return bool(scalar(db, "SELECT to_regclass(:name) IS NOT NULL", {"name": relation_name}))


def column_exists(db: Any, table_name: str, column_name: str) -> bool:
    return bool(
        scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
            """,
            {"table_name": table_name, "column_name": column_name},
        )
    )


def safe_count(db: Any, relation_name: str) -> int | None:
    if not exists_relation(db, relation_name):
        return None
    return int(scalar(db, f"SELECT COUNT(*) FROM {relation_name}") or 0)


def audit() -> dict[str, Any]:
    engine = create_engine(DATABASE_URL_OBJ, pool_pre_ping=True, future=True)
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": {
            "host": database_url_host(),
            "database": database_url_database(),
            "is_neon": database_url_is_neon(),
            "url": masked_database_url(),
        },
        "issues": [],
        "warnings": [],
        "phases": {},
    }

    with engine.connect() as db:
        report["phases"]["inventory"] = {
            "tables": rows(
                db,
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """,
            ),
            "views": rows(
                db,
                """
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = 'public'
                ORDER BY table_name
                """,
            ),
            "primary_keys": rows(
                db,
                """
                SELECT tc.table_name, kcu.column_name, tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY tc.table_name, kcu.ordinal_position
                """,
            ),
            "foreign_keys": rows(
                db,
                """
                SELECT
                    tc.table_name AS source_table,
                    kcu.column_name AS source_column,
                    ccu.table_name AS target_table,
                    ccu.column_name AS target_column,
                    tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name, kcu.column_name
                """,
            ),
        }

        fact_rows = int(scalar(db, "SELECT COUNT(*) FROM fact_metre") or 0)
        fact_amounts = rows(
            db,
            """
            SELECT
                COALESCE(SUM(capex_local), 0) AS capex_local,
                COALESCE(SUM(capex_import), 0) AS capex_import,
                COALESCE(SUM(capex_optimise), 0) AS capex_optimise,
                COALESCE(SUM(economie), 0) AS economie
            FROM fact_metre
            """,
        )[0]
        missing_fact = rows(
            db,
            """
            SELECT
                COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(lot), ''), NULL) IS NULL) AS sans_lot,
                COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(sous_lot), ''), NULLIF(TRIM(sous_lot_id), ''), NULL) IS NULL) AS sans_sous_lot,
                COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(code_article), ''), NULLIF(TRIM(article_id), ''), NULL) IS NULL) AS sans_article,
                COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(batiment), ''), NULL) IS NULL) AS sans_batiment,
                COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(niveau), ''), NULL) IS NULL) AS sans_niveau,
                COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(appartement_id), ''), NULLIF(TRIM(appartement_code), ''), NULLIF(TRIM(appart), ''), NULL) IS NULL) AS sans_appartement,
                COUNT(*) FILTER (WHERE COALESCE(NULLIF(TRIM(piece), ''), NULLIF(TRIM(piece_code), ''), NULL) IS NULL) AS sans_piece
            FROM fact_metre
            """,
        )[0]
        duplicate_count = int(
            scalar(
                db,
                """
                WITH d AS (
                    SELECT
                        batiment,
                        niveau,
                        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, '')) AS appartement,
                        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, '')) AS piece,
                        lot,
                        COALESCE(NULLIF(sous_lot_id, ''), NULLIF(sous_lot, '')) AS sous_lot_key,
                        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, '')) AS article_key,
                        designation,
                        COUNT(*) AS duplicate_count
                    FROM fact_metre
                    GROUP BY batiment, niveau,
                        COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, '')),
                        COALESCE(NULLIF(piece, ''), NULLIF(piece_code, '')),
                        lot,
                        COALESCE(NULLIF(sous_lot_id, ''), NULLIF(sous_lot, '')),
                        COALESCE(NULLIF(code_article, ''), NULLIF(article_id, '')),
                        designation
                    HAVING COUNT(*) > 1
                )
                SELECT COUNT(*) FROM d
                """,
            )
            or 0
        )
        report["phases"]["fact_metre"] = {
            "rows": fact_rows,
            "amounts": fact_amounts,
            "missing": missing_fact,
            "duplicate_business_keys": duplicate_count,
        }

        report["phases"]["lot"] = {
            "fact_distinct": int(scalar(db, "SELECT COUNT(DISTINCT lot) FROM fact_metre") or 0),
            "dim_rows": safe_count(db, "dim_lot"),
            "active_rows": safe_count(db, "vw_dim_lot_active"),
            "fact_missing_dim": rows(
                db,
                """
                SELECT DISTINCT f.lot
                FROM fact_metre f
                LEFT JOIN dim_lot d
                  ON UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
                WHERE f.lot IS NOT NULL AND d.lot IS NULL
                ORDER BY f.lot
                """,
            ),
            "dim_unused": rows(
                db,
                """
                SELECT d.lot
                FROM dim_lot d
                LEFT JOIN fact_metre f
                  ON UPPER(TRIM(COALESCE(f.lot, ''))) = UPPER(TRIM(COALESCE(d.lot, '')))
                WHERE f.id_ligne IS NULL
                ORDER BY d.lot
                """,
            ),
            "historical_candidates": rows(
                db,
                """
                SELECT d.lot
                FROM dim_lot d
                WHERE d.lot LIKE 'LOT %'
                   OR d.lot IN ('LOT ELECTRICITE', 'LOT TECHNIQUE', 'LOT 1', 'LOT 4', 'LOT 6')
                ORDER BY d.lot
                """,
            ),
            "bim_active": rows(
                db,
                """
                SELECT DISTINCT lot
                FROM fact_metre
                WHERE lot LIKE 'LOT_%'
                ORDER BY lot
                """,
            ),
        }

        report["phases"]["sous_lot"] = {
            "fact_distinct": int(scalar(db, "SELECT COUNT(DISTINCT COALESCE(NULLIF(sous_lot_id, ''), NULLIF(sous_lot, ''))) FROM fact_metre") or 0),
            "dim_rows": safe_count(db, "dim_sous_lot_complet"),
            "active_rows": safe_count(db, "vw_dim_sous_lot_active"),
            "fact_missing_dim": rows(
                db,
                """
                SELECT DISTINCT f.lot, COALESCE(NULLIF(f.sous_lot_id, ''), NULLIF(f.sous_lot, '')) AS sous_lot_key
                FROM fact_metre f
                LEFT JOIN dim_sous_lot_complet d
                  ON UPPER(TRIM(COALESCE(f.sous_lot_id, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
                  OR UPPER(TRIM(COALESCE(f.sous_lot, ''))) = UPPER(TRIM(COALESCE(d.sous_lot_id, '')))
                WHERE COALESCE(NULLIF(f.sous_lot_id, ''), NULLIF(f.sous_lot, '')) IS NOT NULL
                  AND d.sous_lot_id IS NULL
                ORDER BY f.lot, sous_lot_key
                """,
            ),
            "duplicates": rows(
                db,
                """
                SELECT sous_lot_id, COUNT(*) AS duplicates
                FROM dim_sous_lot_complet
                GROUP BY sous_lot_id
                HAVING COUNT(*) > 1
                ORDER BY duplicates DESC
                """,
            ),
        }

        report["phases"]["article"] = {
            "fact_distinct": int(scalar(db, "SELECT COUNT(DISTINCT COALESCE(NULLIF(code_article, ''), NULLIF(article_id, ''))) FROM fact_metre") or 0),
            "dim_rows": safe_count(db, "dim_article_bpu"),
            "active_rows": safe_count(db, "vw_dim_article_bpu_active"),
            "fact_missing_dim": rows(
                db,
                """
                SELECT DISTINCT f.lot, f.sous_lot_id, f.code_article, f.article_id, f.designation
                FROM fact_metre f
                LEFT JOIN dim_article_bpu d
                  ON UPPER(TRIM(COALESCE(f.code_article, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
                  OR UPPER(TRIM(COALESCE(f.article_id, ''))) = UPPER(TRIM(COALESCE(d.code_article, '')))
                WHERE COALESCE(NULLIF(f.code_article, ''), NULLIF(f.article_id, '')) IS NOT NULL
                  AND d.code_article IS NULL
                ORDER BY f.lot, f.sous_lot_id, f.code_article, f.article_id
                LIMIT 100
                """,
            ),
            "format_collisions": rows(
                db,
                """
                WITH n AS (
                    SELECT
                        code_article,
                        REGEXP_REPLACE(UPPER(code_article), '[^A-Z0-9]', '', 'g') AS normalized_code
                    FROM dim_article_bpu
                )
                SELECT normalized_code, COUNT(DISTINCT code_article) AS variants
                FROM n
                GROUP BY normalized_code
                HAVING COUNT(DISTINCT code_article) > 1
                ORDER BY variants DESC, normalized_code
                """,
            ),
        }

        piece_appartement_column = None
        for candidate in ("appartement_id", "appart", "appartement_code"):
            if column_exists(db, "dim_piece", candidate):
                piece_appartement_column = candidate
                break
        appartement_key_column = "appartement_id" if column_exists(db, "dim_appartement", "appartement_id") else None

        if piece_appartement_column and appartement_key_column:
            appartements_sans_piece = rows(
                db,
                f"""
                SELECT da.{appartement_key_column} AS appartement_id
                FROM dim_appartement da
                LEFT JOIN dim_piece dp ON dp.{piece_appartement_column} = da.{appartement_key_column}
                WHERE dp.piece_id IS NULL
                ORDER BY da.{appartement_key_column}
                LIMIT 100
                """,
            )
            pieces_sans_appartement = rows(
                db,
                f"""
                SELECT dp.piece_id, {('dp.piece_nom' if column_exists(db, 'dim_piece', 'piece_nom') else 'dp.piece')} AS piece_nom
                FROM dim_piece dp
                LEFT JOIN dim_appartement da ON da.{appartement_key_column} = dp.{piece_appartement_column}
                WHERE dp.{piece_appartement_column} IS NOT NULL
                  AND da.{appartement_key_column} IS NULL
                ORDER BY dp.piece_id
                LIMIT 100
                """,
            )
        else:
            appartements_sans_piece = []
            pieces_sans_appartement = []
            report["warnings"].append("Audit BIM partiel: cle appartement dim_piece/dim_appartement absente ou non standard.")

        report["phases"]["bim"] = {
            "counts": rows(
                db,
                """
                SELECT
                    COUNT(DISTINCT batiment) AS batiments,
                    COUNT(DISTINCT niveau) AS niveaux,
                    COUNT(DISTINCT COALESCE(NULLIF(appartement_id, ''), NULLIF(appartement_code, ''), NULLIF(appart, ''))) AS appartements,
                    COUNT(DISTINCT COALESCE(NULLIF(piece, ''), NULLIF(piece_code, ''))) AS pieces
                FROM fact_metre
                """,
            )[0],
            "appartements_sans_piece": appartements_sans_piece,
            "pieces_sans_appartement": pieces_sans_appartement,
            "join_columns": {
                "dim_piece": piece_appartement_column,
                "dim_appartement": appartement_key_column,
            },
        }

        report["phases"]["powerbi_ready"] = {
            "active_dimensions": rows(
                db,
                """
                SELECT 'vw_dim_lot_active' AS view_name, COUNT(*) AS rows_count, COUNT(DISTINCT lot) AS distinct_count FROM vw_dim_lot_active
                UNION ALL SELECT 'vw_dim_sous_lot_active', COUNT(*), COUNT(DISTINCT sous_lot_id) FROM vw_dim_sous_lot_active
                UNION ALL SELECT 'vw_dim_article_bpu_active', COUNT(*), COUNT(DISTINCT code_article) FROM vw_dim_article_bpu_active
                """,
            )
            if all(exists_relation(db, view) for view in ("vw_dim_lot_active", "vw_dim_sous_lot_active", "vw_dim_article_bpu_active"))
            else [],
        }

        piece_surface_expr = "dp.surface_m2" if column_exists(db, "dim_piece", "surface_m2") else "0::numeric"
        appartement_surface_expr = "da.surface_m2" if column_exists(db, "dim_appartement", "surface_m2") else "0::numeric"
        if piece_surface_expr == "0::numeric":
            report["warnings"].append("Audit KPI surface partiel: dim_piece.surface_m2 absente.")
        if appartement_surface_expr == "0::numeric":
            report["warnings"].append("Audit KPI surface partiel: dim_appartement.surface_m2 absente.")

        report["phases"]["kpis"] = rows(
            db,
            f"""
            SELECT
                COALESCE(SUM(f.capex_local), 0) AS capex_local,
                COALESCE(SUM(f.capex_import), 0) AS capex_import,
                COALESCE(SUM(f.capex_optimise), 0) AS capex_optimise,
                COALESCE(SUM(f.economie), 0) AS economie,
                CASE WHEN COALESCE(SUM(f.capex_local), 0) = 0 THEN 0
                     ELSE COALESCE(SUM(f.economie), 0) / NULLIF(SUM(f.capex_local), 0)
                END AS taux_economie,
                COALESCE(SUM(DISTINCT {piece_surface_expr}), 0) AS surface_totale,
                COALESCE(AVG(DISTINCT {appartement_surface_expr}), 0) AS surface_moyenne_appartement,
                CASE WHEN COALESCE(SUM(DISTINCT {piece_surface_expr}), 0) = 0 THEN 0
                     ELSE COALESCE(SUM(f.capex_optimise), 0) / NULLIF(SUM(DISTINCT {piece_surface_expr}), 0)
                END AS capex_m2
            FROM fact_metre f
            LEFT JOIN dim_piece dp ON dp.piece_id = f.piece_id
            LEFT JOIN dim_appartement da ON da.appartement_id = f.appartement_id
            """,
        )[0]

        report["phases"]["robustness_tests"] = rows(
            db,
            """
            WITH test_filters AS (
                SELECT 'BAT_01'::text AS batiment, NULL::text AS niveau, NULL::text AS appartement, NULL::text AS piece
                UNION ALL SELECT 'BAT_01', 'N1', 'A101', 'CHAMBRE_1'
                UNION ALL SELECT 'BAT_01', 'N2', 'A201', 'SEJOUR'
                UNION ALL SELECT 'BAT_01', 'N3', 'B301', 'SDB_1'
            )
            SELECT
                t.batiment,
                t.niveau,
                t.appartement,
                t.piece,
                COUNT(f.*) AS nb_lignes,
                COALESCE(SUM(f.capex_local), 0) AS capex_local,
                COALESCE(SUM(f.capex_optimise), 0) AS capex_optimise,
                COALESCE(SUM(f.economie), 0) AS economie
            FROM test_filters t
            LEFT JOIN fact_metre f
                ON f.batiment = t.batiment
               AND (t.niveau IS NULL OR f.niveau = t.niveau)
               AND (
                    t.appartement IS NULL
                    OR COALESCE(NULLIF(f.appartement_id, ''), NULLIF(f.appartement_code, ''), NULLIF(f.appart, '')) = t.appartement
               )
               AND (
                    t.piece IS NULL
                    OR COALESCE(NULLIF(f.piece, ''), NULLIF(f.piece_code, '')) = t.piece
               )
            GROUP BY t.batiment, t.niveau, t.appartement, t.piece
            ORDER BY t.batiment, t.niveau, t.appartement, t.piece
            """,
        )

    score = score_report(report)
    report["quality"] = score
    return report


def score_report(report: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = list(report.get("warnings") or [])
    phases = report["phases"]

    if not report["database"]["is_neon"]:
        issues.append("La connexion utilisee n'est pas Neon.")

    fact = phases.get("fact_metre", {})
    if int(fact.get("rows") or 0) == 0:
        issues.append("fact_metre est vide.")

    missing = fact.get("missing", {})
    for key in ("sans_lot", "sans_batiment", "sans_niveau", "sans_appartement", "sans_piece"):
        if int(missing.get(key) or 0) > 0:
            issues.append(f"fact_metre contient {missing[key]} lignes {key}.")
    for key in ("sans_sous_lot", "sans_article"):
        if int(missing.get(key) or 0) > 0:
            warnings.append(f"fact_metre contient {missing[key]} lignes {key}.")

    if int(fact.get("duplicate_business_keys") or 0) > 0:
        warnings.append(f"{fact['duplicate_business_keys']} groupes de doublons metier detectes.")

    for phase_name in ("lot", "sous_lot", "article"):
        phase = phases.get(phase_name, {})
        if phase.get("active_rows") is None:
            issues.append(f"Vue active manquante pour {phase_name}.")
        if phase.get("fact_missing_dim"):
            issues.append(f"{phase_name}: valeurs presentes dans fact_metre absentes du referentiel.")
        if phase_name == "article" and int(phase.get("active_rows") or 0) == 0:
            warnings.append("vw_dim_article_bpu_active est vide: verifier code_article vs article_id.")

    for row in phases.get("robustness_tests", []):
        if row.get("niveau") and int(row.get("nb_lignes") or 0) == 0:
            warnings.append(
                f"Test filtre sans ligne: {row.get('batiment')} / {row.get('niveau')} / {row.get('appartement')} / {row.get('piece')}"
            )

    if issues:
        grade = "D" if len(issues) >= 3 else "C"
    elif warnings:
        grade = "B"
    else:
        grade = "A"

    return {
        "grade": grade,
        "issues": issues,
        "warnings": warnings,
        "target": "A",
    }


def write_report(report: dict[str, Any]) -> None:
    JSON_OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    phases = report["phases"]
    quality = report["quality"]
    lines = [
        "# Audit Neon - SP2I CAPEX MPEMBA V2",
        "",
        f"Date UTC : `{report['generated_at']}`",
        f"Base : `{report['database']['database']}`",
        f"Host : `{report['database']['host']}`",
        f"Neon : `{report['database']['is_neon']}`",
        "",
        f"## Niveau de qualite : {quality['grade']}",
        "",
        "Objectif cible : A",
        "",
        "## KPI SQL",
        "",
        "```json",
        json.dumps(phases.get("kpis", {}), indent=2, ensure_ascii=False, default=str),
        "```",
        "",
        "## FACT_METRE",
        "",
        f"Lignes : `{phases.get('fact_metre', {}).get('rows')}`",
        "",
        "Montants :",
        "",
        "```json",
        json.dumps(phases.get("fact_metre", {}).get("amounts", {}), indent=2, ensure_ascii=False, default=str),
        "```",
        "",
        "Manquants :",
        "",
        "```json",
        json.dumps(phases.get("fact_metre", {}).get("missing", {}), indent=2, ensure_ascii=False, default=str),
        "```",
        "",
        "## Dimensions actives",
        "",
        "```json",
        json.dumps(phases.get("powerbi_ready", {}).get("active_dimensions", []), indent=2, ensure_ascii=False, default=str),
        "```",
        "",
        "## Tests de robustesse",
        "",
        "```json",
        json.dumps(phases.get("robustness_tests", []), indent=2, ensure_ascii=False, default=str),
        "```",
        "",
        "## Anomalies",
        "",
    ]
    if quality["issues"]:
        lines.extend(f"- {issue}" for issue in quality["issues"])
    else:
        lines.append("- Aucune anomalie bloquante.")
    lines.extend(["", "## Risques residuels", ""])
    if quality["warnings"]:
        lines.extend(f"- {warning}" for warning in quality["warnings"])
    else:
        lines.append("- Aucun risque residuel majeur detecte par l'audit SQL.")
    lines.extend(
        [
            "",
            "## Requetes correctives SQL",
            "",
            "- Installer ou rafraichir les vues actives avec `sql/powerbi/001_powerbi_views.sql`.",
            "- Utiliser `vw_dim_lot_active`, `vw_dim_sous_lot_active`, `vw_dim_article_bpu_active` dans Power BI.",
            "- Si `vw_dim_article_bpu_active` est vide, aligner `fact_metre.code_article` avec `dim_article_bpu.code_article` ou charger `dim_article_bpu` depuis le master.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    result = audit()
    write_report(result)
    print(json.dumps({"grade": result["quality"]["grade"], "issues": result["quality"]["issues"], "warnings": result["quality"]["warnings"]}, ensure_ascii=False))
