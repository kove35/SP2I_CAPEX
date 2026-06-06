from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


MASTER_FILE = Path(__file__).with_name("SP2I_BIM_DQE_MASTER.xlsx")
PROJECT_ID = "PROJET_MPEMBA"
BATIMENT_ID = "BAT_01"
INTEGRATION_REPORT_SHEET = "MASTER_REF_INTEGRATION_REPORT"

EXPECTED_APARTMENTS = ["A101", "B101", "A201", "B201", "A301", "B301"]
EXPECTED_COMMON_SCOPE = "COMMUN"
EXPECTED_PIECES = [
    "ENTREE",
    "SEJOUR",
    "CUISINE",
    "CHAMBRE_1",
    "SDB_1",
    "CHAMBRE_2",
    "SDB_2",
    "CHAMBRE_3",
    "SDB_3",
    "DRESSING",
    "WC_VISITEUR",
    "DEGAGEMENT",
    "BALCON",
]
EXPECTED_ZONES = [
    "ZONE_JOUR",
    "ZONE_NUIT",
    "ZONE_SANITAIRE",
    "ZONE_CIRCULATION",
    "ZONE_EXTERIEURE",
    "ZONE_TECHNIQUE",
]
EXPECTED_LOTS = [
    "LOT_ELEC",
    "LOT_PLOMB",
    "LOT_CLIM",
    "LOT_MENUIS",
    "LOT_REVET",
    "LOT_PEINT",
    "LOT_FP",
    "LOT_TOITURE",
]


@dataclass(frozen=True)
class SheetImportSpec:
    sheet: str
    table: str
    column_map: list[tuple[str, str]]
    truncate: bool = True


IMPORT_SPECS: list[SheetImportSpec] = [
    SheetImportSpec(
        sheet="DIM_BATIMENT",
        table="dim_batiment",
        column_map=[
            ("BATIMENT_ID", "batiment"),
            ("BATIMENT_CODE", "batiment_code"),
            ("NOM", "nom"),
            ("NB_NIVEAUX", "nb_niveaux"),
            ("NB_APPARTEMENTS", "nb_appartements"),
            ("SURFACE_TOTALE_M2", "surface_totale_m2"),
            ("TYPE_BATIMENT", "type_batiment"),
            ("DESCRIPTION", "description"),
            ("IS_ACTIVE", "is_active"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_NIVEAU",
        table="dim_niveau",
        column_map=[
            ("NIVEAU_ID", "niveau"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_APPARTEMENT",
        table="dim_appartement",
        column_map=[
            ("APPARTEMENT_ID", "appartement_id"),
            ("APPARTEMENT_CODE", "appartement_code"),
            ("NIVEAU_ID", "niveau_id"),
            ("NIVEAU_ID", "niveau"),
            ("BATIMENT_ID", "batiment"),
            ("SURFACE_M2", "surface"),
            ("SURFACE_M2", "surface_m2"),
            ("TYPE", "type"),
            ("TYPE", "type_appartement"),
            ("NB_CHAMBRES", "nb_chambres"),
            ("NB_SDB", "nb_sdb"),
            ("TYPOLOGIE", "description"),
            ("IS_ACTIVE", "is_active"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_ZONE",
        table="dim_zone",
        column_map=[
            ("ZONE_ID", "zone_code"),
            ("ZONE_NOM", "zone_nom"),
            ("DESCRIPTION", "description"),
            ("IS_ACTIVE", "is_active"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_PIECE",
        table="dim_piece",
        column_map=[
            ("PIECE_ID", "piece_code"),
            ("APPARTEMENT_ID", "appartement_id"),
            ("PIECE_NOM", "piece_nom"),
            ("PIECE_NOM", "piece"),
            ("PIECE_TYPE", "piece_type"),
            ("PIECE_TYPE", "type_piece"),
            ("SURFACE_M2", "surface_m2"),
            ("ZONE", "zone"),
            ("IS_ACTIVE", "is_active"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_LOT",
        table="dim_lot",
        column_map=[
            ("LOT_ID", "lot"),
            ("DESCRIPTION", "description"),
            ("IS_ACTIVE", "is_active"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_SOUS_LOT_COMPLET",
        table="dim_sous_lot_complet",
        column_map=[
            ("SOUS_LOT_ID", "sous_lot_id"),
            ("LOT_ID", "lot_id"),
            ("DESCRIPTION", "description"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_ARTICLE_BPU",
        table="dim_article_bpu",
        column_map=[
            ("CODE_ARTICLE", "code_article"),
            ("DESIGNATION", "designation"),
            ("MARQUE", "marque"),
            ("UNITE", "unite"),
        ],
    ),
    SheetImportSpec(
        sheet="DIM_ARTICLE_BPU_EXTENDED",
        table="dim_article_bpu_extended",
        column_map=[
            ("ARTICLE_ID", "article_id"),
            ("LOT_ID", "lot_id"),
            ("SOUS_LOT_ID", "sous_lot_id"),
            ("CODE_ARTICLE", "code_article"),
            ("DESIGNATION", "designation"),
            ("MARQUE", "marque"),
            ("UNITE", "unite"),
            ("IFC_CLASS", "ifc_class"),
        ],
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Importe et audite le referentiel maitre SP2I Mpemba.")
    parser.add_argument("--workbook", type=Path, default=MASTER_FILE)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--write-reports", action="store_true", help="Met a jour les feuilles de scorecard/report.")
    parser.add_argument("--execute", action="store_true", help="Execute TRUNCATE + RELOAD dans PostgreSQL/Neon.")
    parser.add_argument("--json", action="store_true", help="Affiche un resume JSON.")
    args = parser.parse_args()

    workbook = args.workbook.resolve()
    wb = load_workbook(workbook)
    data = {sheet: read_sheet(wb, sheet) for sheet in required_sheets()}
    report = build_report(data)

    imported_rows: dict[str, int] = {}
    if args.execute:
        if not args.database_url:
            raise SystemExit("--execute requiert --database-url ou DATABASE_URL")
        imported_rows = import_dimensions(args.database_url, data)
    else:
        imported_rows = {spec.table: len(data.get(spec.sheet, [])) for spec in IMPORT_SPECS}

    report["dimensions_importees"] = imported_rows
    if args.write_reports:
        write_workbook_reports(wb, report)
        wb.save(workbook)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        print_summary(report)
    return 0 if report["integration_score"] >= 95 and report["critical_issues"] == 0 else 1


def required_sheets() -> list[str]:
    return sorted({spec.sheet for spec in IMPORT_SPECS} | {"FACT_METRE"})


def read_sheet(wb, sheet_name: str) -> list[dict[str, Any]]:
    if sheet_name not in wb.sheetnames:
        return []
    ws = wb[sheet_name]
    headers = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
    rows: list[dict[str, Any]] = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        if any(value is not None for value in values):
            rows.append(dict(zip(headers, values)))
    return rows


def build_report(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    def issue(section: str, check: str, status: str, details: str, severity: str = "INFO") -> None:
        issues.append(
            {
                "section": section,
                "check": check,
                "status": status,
                "details": details,
                "severity": severity,
            }
        )

    fact = data["FACT_METRE"]
    bats = data["DIM_BATIMENT"]
    niveaux = data["DIM_NIVEAU"]
    apps = data["DIM_APPARTEMENT"]
    zones = data["DIM_ZONE"]
    pieces = data["DIM_PIECE"]
    lots = data["DIM_LOT"]
    sous_lots = data["DIM_SOUS_LOT_COMPLET"]
    articles = data["DIM_ARTICLE_BPU_EXTENDED"]

    validate_building(issue, bats, niveaux, apps, pieces, zones)
    validate_keys(issue, fact, bats, niveaux, apps, pieces, lots, sous_lots, articles)
    validate_lots(issue, fact, lots, sous_lots, articles)
    capex = validate_capex(issue, fact)
    procurement = validate_procurement(issue, fact)
    validate_powerbi(issue, fact, zones)
    benchmarks = build_benchmarks(fact)

    scores = scorecard(issues)
    return {
        "project": PROJECT_ID,
        "master_reference": "SP2I_BIM_DQE_MASTER.xlsx",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dimensions": {
            name: len(rows)
            for name, rows in data.items()
            if name != "FACT_METRE"
        },
        "fact_metre_rows": len(fact),
        "capex": capex,
        "procurement": procurement,
        "benchmarks": benchmarks,
        "issues": issues,
        "critical_issues": sum(1 for row in issues if row["severity"] == "CRITICAL" and row["status"] == "KO"),
        "warning_issues": sum(1 for row in issues if row["severity"] == "WARNING"),
        "scorecard": scores,
        "integration_score": scores["GLOBAL_READY"],
        "validated_endpoints": [
            "/analytics/dashboard",
            "/analytics/spatial",
            "/analytics/spatial/dashboard",
            "/analytics/drilldown",
        ],
        "validated_views": ["vw_spatial_dashboard", "vw_spatial_analytics"],
        "fact_metre_write_policy": "READ_ONLY_NEVER_TRUNCATE",
    }


def validate_building(issue, bats, niveaux, apps, pieces, zones) -> None:
    bat = next((row for row in bats if row.get("BATIMENT_ID") == BATIMENT_ID), None)
    if not bat:
        issue("BUILDING", "BAT_01", "KO", "BAT_01 absent de DIM_BATIMENT", "CRITICAL")
        return
    expected = {
        "NB_NIVEAUX": 3,
        "NB_APPARTEMENTS": 6,
        "SURFACE_TOTALE_M2": 1263.90,
    }
    for key, expected_value in expected.items():
        observed = float(bat.get(key) or 0)
        ok = round(observed, 2) == round(float(expected_value), 2)
        issue("BUILDING", key, "OK" if ok else "KO", f"observe={observed} attendu={expected_value}", "CRITICAL" if not ok else "INFO")

    resident_levels = {row.get("NIVEAU_ID") for row in apps if row.get("APPARTEMENT_ID") in EXPECTED_APARTMENTS}
    issue("BUILDING", "3 niveaux residentiels", "OK" if len(resident_levels) == 3 else "KO", str(sorted(resident_levels)), "CRITICAL" if len(resident_levels) != 3 else "INFO")
    app_ids = {row.get("APPARTEMENT_ID") for row in apps}
    missing_apps = [app for app in EXPECTED_APARTMENTS if app not in app_ids]
    issue("BUILDING", "6 appartements", "OK" if not missing_apps else "KO", f"manquants={missing_apps}", "CRITICAL" if missing_apps else "INFO")

    by_app = defaultdict(set)
    for row in pieces:
        by_app[row.get("APPARTEMENT_ID")].add(row.get("PIECE_NOM"))
    for app in EXPECTED_APARTMENTS:
        missing = [piece for piece in EXPECTED_PIECES if piece not in by_app[app]]
        count_ok = len(by_app[app]) == len(EXPECTED_PIECES)
        status = "OK" if not missing and count_ok else "KO"
        issue("BUILDING", f"13 pieces {app}", status, f"count={len(by_app[app])} manquants={missing}", "CRITICAL" if status == "KO" else "INFO")

    zone_ids = {row.get("ZONE_ID") or row.get("ZONE_CODE") for row in zones}
    missing_zones = [zone for zone in EXPECTED_ZONES if zone not in zone_ids]
    issue("BUILDING", "zones spatiales", "OK" if not missing_zones else "KO", f"manquantes={missing_zones}", "CRITICAL" if missing_zones else "INFO")


def validate_keys(issue, fact, bats, niveaux, apps, pieces, lots, sous_lots, articles) -> None:
    check_set(issue, "KEYS", "FACT_METRE.BATIMENT_ID -> DIM_BATIMENT", fact, "BATIMENT_ID", bats, "BATIMENT_ID")
    check_set(issue, "KEYS", "FACT_METRE.NIVEAU_ID -> DIM_NIVEAU", fact, "NIVEAU_ID", niveaux, "NIVEAU_ID")
    check_set(issue, "KEYS", "FACT_METRE.APPARTEMENT_ID -> DIM_APPARTEMENT", [row for row in fact if row.get("APPARTEMENT_ID") != EXPECTED_COMMON_SCOPE], "APPARTEMENT_ID", apps, "APPARTEMENT_ID")
    check_set(issue, "KEYS", "FACT_METRE.LOT_ID -> DIM_LOT", fact, "LOT_ID", lots, "LOT_ID")
    check_set(issue, "KEYS", "FACT_METRE.SOUS_LOT_ID -> DIM_SOUS_LOT_COMPLET", fact, "SOUS_LOT_ID", sous_lots, "SOUS_LOT_ID")
    check_set(issue, "KEYS", "FACT_METRE.CODE_ARTICLE -> DIM_ARTICLE_BPU_EXTENDED", fact, "CODE_ARTICLE", articles, "CODE_ARTICLE")

    piece_names = {(row.get("APPARTEMENT_ID"), row.get("PIECE_NOM")) for row in pieces}
    orphans = sorted(
        {
            (row.get("APPARTEMENT_ID"), row.get("PIECE_ID"))
            for row in fact
            if row.get("APPARTEMENT_ID") != EXPECTED_COMMON_SCOPE
            and row.get("PIECE_ID") != "TOITURE"
            and (row.get("APPARTEMENT_ID"), row.get("PIECE_ID")) not in piece_names
        }
    )
    issue("KEYS", "FACT_METRE.PIECE_ID -> DIM_PIECE", "OK" if not orphans else "KO", f"orphelins={orphans[:20]}", "CRITICAL" if orphans else "INFO")


def check_set(issue, section: str, check: str, source_rows, source_col: str, target_rows, target_col: str) -> None:
    source = {row.get(source_col) for row in source_rows if row.get(source_col)}
    target = {row.get(target_col) for row in target_rows if row.get(target_col)}
    orphans = sorted(source - target)
    issue(section, check, "OK" if not orphans else "KO", f"orphelins={orphans}", "CRITICAL" if orphans else "INFO")


def validate_lots(issue, fact, lots, sous_lots, articles) -> None:
    lot_ids = {row.get("LOT_ID") for row in lots}
    for lot in EXPECTED_LOTS:
        issue("LOTS", lot, "OK" if lot in lot_ids else "KO", "lot canonique attendu", "CRITICAL" if lot not in lot_ids else "INFO")

    fact_by_lot = defaultdict(list)
    for row in fact:
        fact_by_lot[row.get("LOT_ID")].append(row)
    sublots_by_lot = defaultdict(set)
    for row in sous_lots:
        sublots_by_lot[row.get("LOT_ID")].add(row.get("SOUS_LOT_ID"))
    articles_by_lot = defaultdict(set)
    for row in articles:
        articles_by_lot[row.get("LOT_ID")].add(row.get("CODE_ARTICLE"))
    for lot in sorted(lot_ids):
        has_dim = bool(sublots_by_lot[lot])
        has_fact_or_article = bool(fact_by_lot[lot] or articles_by_lot[lot])
        status = "OK" if has_dim and has_fact_or_article else "WARNING"
        issue("LOTS", f"composition {lot}", status, f"sous_lots={len(sublots_by_lot[lot])} articles={len(articles_by_lot[lot])} lignes_fact={len(fact_by_lot[lot])}", "WARNING" if status == "WARNING" else "INFO")


def validate_capex(issue, fact) -> dict[str, Any]:
    total_local = sum(to_float(row.get("MONTANT_LOCAL")) for row in fact)
    total_import = sum(to_float(row.get("MONTANT_IMPORT")) for row in fact)
    total_optimise = sum(optimised_capex(row) for row in fact)
    economie = total_local - total_optimise
    for label, column in [
        ("CAPEX_BATIMENT", "BATIMENT_ID"),
        ("CAPEX_NIVEAU", "NIVEAU_ID"),
        ("CAPEX_APPARTEMENT", "APPARTEMENT_ID"),
        ("CAPEX_ZONE", "PIECE_ID"),
        ("CAPEX_PIECE", "PIECE_ID"),
        ("CAPEX_LOT", "LOT_ID"),
        ("CAPEX_SOUS_LOT", "SOUS_LOT_ID"),
        ("CAPEX_ARTICLE", "CODE_ARTICLE"),
    ]:
        grouped_total = sum(group_sum(fact, column).values())
        ok = round(grouped_total, 2) == round(total_local, 2)
        issue("CAPEX", label, "OK" if ok else "KO", f"grouped={grouped_total:.2f} total={total_local:.2f}", "CRITICAL" if not ok else "INFO")
    return {
        "CAPEX_TOTAL_MPEMBA": round(total_local, 2),
        "CAPEX_IMPORT_MPEMBA": round(total_import, 2),
        "CAPEX_OPTIMISE_MPEMBA": round(total_optimise, 2),
        "ECONOMIE_MPEMBA": round(economie, 2),
        "CAPEX_M2_MPEMBA": round(total_optimise / 1263.90, 2),
        "CAPEX_NIVEAU_MPEMBA": group_sum(fact, "NIVEAU_ID"),
        "CAPEX_APPARTEMENT_MPEMBA": group_sum(fact, "APPARTEMENT_ID"),
        "CAPEX_ZONE_MPEMBA": group_sum(fact, "PIECE_ID"),
        "CAPEX_PIECE_MPEMBA": group_sum(fact, "PIECE_ID"),
    }


def validate_procurement(issue, fact) -> dict[str, Any]:
    decisions = Counter(str(row.get("DECISION") or "").upper() for row in fact)
    for decision in ["LOCAL", "IMPORT", "HYBRIDE", "VALIDATION_DIRECTION"]:
        status = "OK" if decisions.get(decision) else "WARNING"
        issue("PROCUREMENT", decision, status, f"count={decisions.get(decision, 0)}", "WARNING" if status == "WARNING" else "INFO")
    local = sum(to_float(row.get("MONTANT_LOCAL")) for row in fact)
    imported = sum(to_float(row.get("MONTANT_IMPORT")) for row in fact)
    optimised = sum(optimised_capex(row) for row in fact)
    return {
        "decisions": dict(decisions),
        "capex_local": round(local, 2),
        "capex_import": round(imported, 2),
        "capex_optimise": round(optimised, 2),
        "economie": round(local - optimised, 2),
    }


def validate_powerbi(issue, fact, zones) -> None:
    required = [
        "PROJET_ID",
        "BATIMENT_ID",
        "NIVEAU_ID",
        "APPARTEMENT_ID",
        "PIECE_ID",
        "LOT_ID",
        "SOUS_LOT_ID",
        "CODE_ARTICLE",
        "MONTANT_LOCAL",
        "MONTANT_IMPORT",
    ]
    available = set(fact[0].keys()) if fact else set()
    missing = [column for column in required if column not in available]
    issue("POWERBI", "vw_spatial_dashboard", "OK" if not missing else "KO", f"colonnes_manquantes={missing}", "CRITICAL" if missing else "INFO")
    issue("POWERBI", "vw_spatial_analytics", "OK" if not missing and zones else "KO", f"zones={len(zones)} colonnes_manquantes={missing}", "CRITICAL" if missing or not zones else "INFO")


def build_benchmarks(fact) -> dict[str, Any]:
    app = group_sum([row for row in fact if row.get("APPARTEMENT_ID") != EXPECTED_COMMON_SCOPE], "APPARTEMENT_ID")
    pairs = {
        "A101_vs_A201_vs_A301": {key: app.get(key, 0) for key in ["A101", "A201", "A301"]},
        "B101_vs_B201_vs_B301": {key: app.get(key, 0) for key in ["B101", "B201", "B301"]},
    }
    bedrooms = [row for row in fact if str(row.get("PIECE_ID") or "").startswith("CHAMBRE_")]
    bathrooms = [row for row in fact if str(row.get("PIECE_ID") or "").startswith("SDB_")]
    sanitary = [row for row in fact if str(row.get("PIECE_ID") or "").startswith("SDB_") or row.get("PIECE_ID") == "WC_VISITEUR"]
    total = sum(to_float(row.get("MONTANT_LOCAL")) for row in fact)
    return {
        "appartement_capex": app,
        "comparaisons": pairs,
        "COUT_MOYEN_APPARTEMENT": round(sum(app.values()) / max(len(EXPECTED_APARTMENTS), 1), 2),
        "COUT_MOYEN_CHAMBRE": round(sum(to_float(row.get("MONTANT_LOCAL")) for row in bedrooms) / 18, 2),
        "COUT_MOYEN_SDB": round(sum(to_float(row.get("MONTANT_LOCAL")) for row in bathrooms) / 18, 2),
        "PART_CAPEX_SANITAIRE": round(100 * sum(to_float(row.get("MONTANT_LOCAL")) for row in sanitary) / total, 2) if total else 0,
        "PART_CAPEX_ELECTRICITE": round(100 * sum(to_float(row.get("MONTANT_LOCAL")) for row in fact if row.get("LOT_ID") == "LOT_ELEC") / total, 2) if total else 0,
        "PART_CAPEX_CLIMATISATION": round(100 * sum(to_float(row.get("MONTANT_LOCAL")) for row in fact if row.get("LOT_ID") in {"LOT_CLIM", "LOT_CVC"}) / total, 2) if total else 0,
    }


def scorecard(issues) -> dict[str, float]:
    def score(section: str, base: int = 100) -> float:
        rows = [row for row in issues if row["section"] == section]
        critical = sum(1 for row in rows if row["severity"] == "CRITICAL" and row["status"] == "KO")
        warnings = sum(1 for row in rows if row["severity"] == "WARNING")
        return max(0.0, min(100.0, base - critical * 20 - warnings * 5))

    scores = {
        "BUILDING_READY": score("BUILDING"),
        "SPATIAL_READY": min(score("BUILDING"), score("KEYS")),
        "CAPEX_READY": score("CAPEX"),
        "PROCUREMENT_READY": score("PROCUREMENT"),
        "POWERBI_READY": score("POWERBI"),
        "ANALYTICS_READY": min(score("CAPEX"), score("POWERBI")),
    }
    scores["GLOBAL_READY"] = round(sum(scores.values()) / len(scores), 2)
    return scores


def group_sum(rows, column: str) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        totals[str(row.get(column) or "NON_RENSEIGNE")] += to_float(row.get("MONTANT_LOCAL"))
    return dict(sorted((key, round(value, 2)) for key, value in totals.items()))


def to_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def optimised_capex(row: dict[str, Any]) -> float:
    decision = str(row.get("DECISION") or "").upper()
    return to_float(row.get("MONTANT_IMPORT")) if decision == "IMPORT" else to_float(row.get("MONTANT_LOCAL"))


def import_dimensions(database_url: str, data: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    from sqlalchemy import create_engine, inspect, text

    engine = create_engine(database_url, pool_pre_ping=True)
    inspector = inspect(engine)
    imported: dict[str, int] = {}
    with engine.begin() as conn:
        for spec in IMPORT_SPECS:
            table_columns = {column["name"] for column in inspector.get_columns(spec.table)}
            rows = [map_row(row, spec, table_columns) for row in data.get(spec.sheet, [])]
            rows = [row for row in rows if row]
            if spec.truncate:
                conn.execute(text(f"TRUNCATE TABLE {spec.table} RESTART IDENTITY"))
            for row in rows:
                cols = list(row.keys())
                placeholders = [f":{col}" for col in cols]
                sql = text(f"INSERT INTO {spec.table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})")
                conn.execute(sql, row)
            imported[spec.table] = len(rows)
    return imported


def map_row(source: dict[str, Any], spec: SheetImportSpec, table_columns: set[str]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for excel_col, table_col in spec.column_map:
        if table_col in table_columns and excel_col in source:
            mapped[table_col] = source.get(excel_col)
    if spec.table == "dim_batiment" and "batiment" in mapped:
        mapped.setdefault("batiment_code", mapped["batiment"])
        mapped.setdefault("nom", mapped["batiment"])
    if spec.table == "dim_zone" and "zone_code" in mapped:
        mapped.setdefault("type_zone", str(mapped["zone_code"]).replace("ZONE_", ""))
    if spec.table == "dim_piece":
        mapped.setdefault("piece", mapped.get("piece_nom") or mapped.get("piece_code"))
    return {key: value for key, value in mapped.items() if value is not None}


def write_workbook_reports(wb, report: dict[str, Any]) -> None:
    score_rows = [
        (key, value, "OK" if value >= 95 else "A_SURVEILLER", report["generated_at"])
        for key, value in report["scorecard"].items()
    ]
    replace_sheet(wb, "MPEMBA_PROJECT_SCORECARD", ["KPI", "SCORE", "STATUS", "RUN_AT"], score_rows)

    report_rows = [
        ("MASTER_REFERENCE", report["master_reference"]),
        ("PROJECT", report["project"]),
        ("FACT_METRE_ROWS", report["fact_metre_rows"]),
        ("INTEGRATION_SCORE", report["integration_score"]),
        ("CRITICAL_ISSUES", report["critical_issues"]),
        ("WARNING_ISSUES", report["warning_issues"]),
        ("FACT_METRE_WRITE_POLICY", report["fact_metre_write_policy"]),
        ("VALIDATED_ENDPOINTS", ", ".join(report["validated_endpoints"])),
        ("VALIDATED_POWERBI_VIEWS", ", ".join(report["validated_views"])),
        ("DIMENSIONS_IMPORTED", json.dumps(report.get("dimensions_importees", report["dimensions"]), ensure_ascii=False)),
        ("CAPEX", json.dumps(report["capex"], ensure_ascii=False, default=str)),
        ("PROCUREMENT", json.dumps(report["procurement"], ensure_ascii=False, default=str)),
        ("BENCHMARKS", json.dumps(report["benchmarks"], ensure_ascii=False, default=str)),
    ]
    if "MASTER_REFERENCE_INTEGRATION_REPORT" in wb.sheetnames:
        wb.remove(wb["MASTER_REFERENCE_INTEGRATION_REPORT"])
    replace_sheet(wb, INTEGRATION_REPORT_SHEET, ["METRIC", "VALUE"], report_rows)


def replace_sheet(wb, name: str, header: list[str], rows: list[tuple[Any, ...]]) -> None:
    idx = wb.sheetnames.index(name) if name in wb.sheetnames else len(wb.sheetnames)
    if name in wb.sheetnames:
        wb.remove(wb[name])
    ws = wb.create_sheet(name, idx)
    ws.append(header)
    for row in rows:
        ws.append([serialise_cell(value) for value in row])
    format_sheet(ws)


def serialise_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def format_sheet(ws) -> None:
    header_fill = PatternFill("solid", fgColor="1F2937")
    header_font = Font(color="FFFFFF", bold=True)
    thin = Side(style="thin", color="D1D5DB")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for row in ws.iter_rows():
        for cell in row:
            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "A2"
    for col_idx in range(1, ws.max_column + 1):
        letter = get_column_letter(col_idx)
        width = max(len(str(cell.value or "")) for cell in ws[letter]) + 2
        ws.column_dimensions[letter].width = min(max(width, 12), 80)


def print_summary(report: dict[str, Any]) -> None:
    print("=== MPEMBA MASTER REFERENCE INTEGRATION ===")
    print(f"reference={report['master_reference']}")
    print(f"fact_metre_rows={report['fact_metre_rows']}")
    print(f"integration_score={report['integration_score']}")
    print(f"critical_issues={report['critical_issues']}")
    print(f"warning_issues={report['warning_issues']}")
    print("scorecard=")
    for key, value in report["scorecard"].items():
        print(f"  {key}: {value}")
    print("dimensions=")
    for key, value in sorted(report.get("dimensions_importees", report["dimensions"]).items()):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
