from __future__ import annotations

import json
import math
import statistics
import time
import traceback
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
MASTER_INPUT = ROOT / "MASTER_REFERENCE_ENTERPRISE.xlsx"
MASTER_V2 = ROOT / "MASTER_REFERENCE_GOVERNANCE_V2.xlsx"
PROCUREMENT_AUDIT = ROOT / "PROCUREMENT_VALIDATION_AUDIT.xlsx"
BENCHMARK_DRIFT_AUDIT = ROOT / "BENCHMARK_DRIFT_AUDIT.xlsx"
LOW_CONFIDENCE_SUPPLIERS = ROOT / "TOP_LOW_CONFIDENCE_SUPPLIERS.xlsx"
MARKET_DRIFT_ANALYSIS = ROOT / "MARKET_DRIFT_ANALYSIS.xlsx"
STATS_PATH = ROOT / "PROCUREMENT_GOVERNANCE_STATS.json"

STATUS_PENDING = "PENDING"
STATUS_PARTIAL = "PARTIAL"
STATUS_VERIFIED = "VERIFIED"
STATUS_REJECTED = "REJECTED"

TODAY = date.today().isoformat()


def number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return default if math.isnan(value) else float(value)
    text = str(value).strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return default


def read_sheet(path: Path, sheet_name: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    wb = load_workbook(path, data_only=True, read_only=True)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Onglet {sheet_name} introuvable dans {path.name}")
    ws = wb[sheet_name]
    headers = [str(cell.value or "").strip() for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    rows: list[dict[str, Any]] = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        payload = {headers[index]: value for index, value in enumerate(values)}
        if any(value not in (None, "") for value in payload.values()):
            rows.append(payload)
    wb.close()
    return rows


def status_for_supplier(row: dict[str, Any]) -> str:
    supplier = str(row.get("FOURNISSEUR_CHINE") or "")
    if not supplier or supplier == "A_VERIFIER_GOUVERNANCE":
        return STATUS_PENDING
    if "REJECT" in supplier.upper():
        return STATUS_REJECTED
    return STATUS_VERIFIED


def fob_status(row: dict[str, Any]) -> str:
    fob = number(row.get("PU_CHINE_FOB_FCFA"))
    price_min = number(row.get("PRICE_MIN_FCFA"))
    if fob <= 0:
        return STATUS_PENDING
    if price_min and (fob < price_min * 0.35 or fob > price_min * 0.95):
        return STATUS_PARTIAL
    return STATUS_VERIFIED


def benchmark_status(row: dict[str, Any]) -> str:
    price_min = number(row.get("PRICE_MIN_FCFA"))
    price_max = number(row.get("PRICE_MAX_FCFA"))
    if price_min <= 0 or price_max <= 0:
        return STATUS_REJECTED
    ratio = price_max / max(price_min, 1)
    if ratio > 8:
        return STATUS_PARTIAL
    return STATUS_VERIFIED if str(row.get("CONFIDENCE_LEVEL")) != "LOW" else STATUS_PARTIAL


def price_variation_level(row: dict[str, Any]) -> str:
    price_min = number(row.get("PRICE_MIN_FCFA"))
    price_max = number(row.get("PRICE_MAX_FCFA"))
    ratio = price_max / max(price_min, 1)
    if ratio >= 10:
        return "EXTREME"
    if ratio >= 5:
        return "HIGH"
    if ratio >= 2.5:
        return "MEDIUM"
    return "LOW"


def drift_score(row: dict[str, Any]) -> float:
    variation = price_variation_level(row)
    confidence = str(row.get("CONFIDENCE_LEVEL") or "LOW")
    risk = str(row.get("RISK_LEVEL") or "HIGH")
    score = {"LOW": 12, "MEDIUM": 30, "HIGH": 55, "EXTREME": 75}[variation]
    if confidence == "LOW":
        score += 18
    elif confidence == "MEDIUM":
        score += 8
    if risk == "HIGH":
        score += 15
    elif risk == "MEDIUM":
        score += 8
    return round(min(score, 100), 2)


def benchmark_confidence(row: dict[str, Any], benchmark_confirmed: str) -> str:
    if benchmark_confirmed == STATUS_VERIFIED and price_variation_level(row) in {"LOW", "MEDIUM"}:
        return "HIGH"
    if benchmark_confirmed in {STATUS_PARTIAL, STATUS_VERIFIED}:
        return "MEDIUM"
    return "LOW"


def validation_status(row: dict[str, Any], supplier: str, fob: str, benchmark: str) -> str:
    base_confidence = str(row.get("CONFIDENCE_LEVEL") or "LOW")
    if STATUS_REJECTED in {supplier, fob, benchmark}:
        return STATUS_REJECTED
    if supplier == fob == benchmark == STATUS_VERIFIED and base_confidence == "HIGH":
        return STATUS_VERIFIED
    if benchmark in {STATUS_VERIFIED, STATUS_PARTIAL} and fob in {STATUS_VERIFIED, STATUS_PARTIAL}:
        return STATUS_PARTIAL
    return STATUS_PENDING


def governed_confidence(row: dict[str, Any], supplier: str, fob: str, benchmark: str, validation: str) -> str:
    if validation == STATUS_VERIFIED and supplier == fob == benchmark == STATUS_VERIFIED:
        return "HIGH"
    if validation == STATUS_REJECTED:
        return "LOW"
    if validation == STATUS_PARTIAL and str(row.get("CONFIDENCE_LEVEL")) != "LOW":
        return "MEDIUM"
    return "LOW" if str(row.get("RISK_LEVEL")) == "HIGH" else "MEDIUM"


def review_required(row: dict[str, Any], validation: str, drift: float) -> str:
    if validation != STATUS_VERIFIED:
        return "YES"
    if drift >= 50:
        return "YES"
    if str(row.get("IMPORTABILITY")) == "HIGH" and str(row.get("FOURNISSEUR_CHINE")) == "A_VERIFIER_GOUVERNANCE":
        return "YES"
    return "NO"


def cockpit_badge(row: dict[str, Any], confidence: str, validation: str, drift: float) -> str:
    if confidence == "LOW" or validation in {STATUS_PENDING, STATUS_REJECTED} or drift >= 65:
        return "RED_CRITICAL"
    if confidence == "MEDIUM" or validation == STATUS_PARTIAL or drift >= 35:
        return "ORANGE_REVIEW"
    return "GREEN_VERIFIED"


def build_governance_rows(master_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    governed: list[dict[str, Any]] = []
    benchmark_rows: list[dict[str, Any]] = []
    procurement_rows: list[dict[str, Any]] = []
    for row in master_rows:
        supplier = status_for_supplier(row)
        fob = fob_status(row)
        benchmark = benchmark_status(row)
        validation = validation_status(row, supplier, fob, benchmark)
        drift = drift_score(row)
        benchmark_conf = benchmark_confidence(row, benchmark)
        confidence = governed_confidence(row, supplier, fob, benchmark, validation)
        review = review_required(row, validation, drift)
        badge = cockpit_badge(row, confidence, validation, drift)
        enriched = {
            **row,
            "SUPPLIER_VERIFIED": supplier,
            "FOB_VERIFIED": fob,
            "LAST_MARKET_CHECK": TODAY,
            "LOCAL_BENCHMARK_CONFIRMED": benchmark,
            "PROCUREMENT_VALIDATED_BY": "DATA_GOVERNANCE_PENDING",
            "VALIDATION_STATUS": validation,
            "BENCHMARK_SOURCE": "MASTER_REFERENCE_ENTERPRISE_PHASE1|DQE_PROJECT_SP2I",
            "BENCHMARK_CONFIDENCE": benchmark_conf,
            "LAST_BENCHMARK_UPDATE": TODAY,
            "MARKET_REGION": "CENTRAL_AFRICA",
            "PRICE_VARIATION_LEVEL": price_variation_level(row),
            "PROCUREMENT_REVIEW_REQUIRED": review,
            "MARKET_DRIFT_SCORE": drift,
            "COCKPIT_CONFIDENCE_BADGE": badge,
            "COCKPIT_WARNING": warning_message(row, confidence, validation, drift),
            "CONFIDENCE_LEVEL": confidence,
        }
        governed.append(enriched)
        benchmark_rows.append({
            "REFERENCE_ID": row.get("REFERENCE_ID"),
            "DESIGNATION_NORMALISEE": row.get("DESIGNATION_NORMALISEE"),
            "FAMILLE": row.get("FAMILLE"),
            "SOUS_FAMILLE": row.get("SOUS_FAMILLE"),
            "PRICE_MIN_FCFA": row.get("PRICE_MIN_FCFA"),
            "PRICE_MAX_FCFA": row.get("PRICE_MAX_FCFA"),
            "BENCHMARK_SOURCE": enriched["BENCHMARK_SOURCE"],
            "BENCHMARK_CONFIDENCE": benchmark_conf,
            "LOCAL_BENCHMARK_CONFIRMED": benchmark,
            "LAST_BENCHMARK_UPDATE": TODAY,
            "MARKET_REGION": "CENTRAL_AFRICA",
            "PRICE_VARIATION_LEVEL": enriched["PRICE_VARIATION_LEVEL"],
            "MARKET_DRIFT_SCORE": drift,
            "DRIFT_STATUS": "CRITICAL" if drift >= 65 else "WATCH" if drift >= 35 else "STABLE",
        })
        procurement_rows.append({
            "REFERENCE_ID": row.get("REFERENCE_ID"),
            "DESIGNATION_NORMALISEE": row.get("DESIGNATION_NORMALISEE"),
            "FOURNISSEUR_CHINE": row.get("FOURNISSEUR_CHINE"),
            "PU_CHINE_FOB_FCFA": row.get("PU_CHINE_FOB_FCFA"),
            "MOQ": row.get("MOQ"),
            "INCOTERM": row.get("INCOTERM"),
            "IMPORTABILITY": row.get("IMPORTABILITY"),
            "SUPPLIER_VERIFIED": supplier,
            "FOB_VERIFIED": fob,
            "VALIDATION_STATUS": validation,
            "PROCUREMENT_REVIEW_REQUIRED": review,
            "PROCUREMENT_RISK": "HIGH" if review == "YES" and confidence == "LOW" else "MEDIUM" if review == "YES" else "LOW",
            "ROI_GOVERNANCE_WARNING": "ROI_DEGRADED_UNTIL_SUPPLIER_FOB_VERIFIED" if review == "YES" else "ROI_USABLE",
        })
    return governed, benchmark_rows, procurement_rows


def warning_message(row: dict[str, Any], confidence: str, validation: str, drift: float) -> str:
    warnings: list[str] = []
    if confidence == "LOW":
        warnings.append("faible confiance")
    if validation != STATUS_VERIFIED:
        warnings.append("validation procurement incomplete")
    if drift >= 65:
        warnings.append("derive marche critique")
    elif drift >= 35:
        warnings.append("derive marche a surveiller")
    if str(row.get("FOURNISSEUR_CHINE")) == "A_VERIFIER_GOUVERNANCE":
        warnings.append("fournisseur Chine non verifie")
    return "; ".join(warnings) if warnings else "reference gouvernee"


def style_sheet(ws) -> None:
    fill = PatternFill("solid", fgColor="0F172A")
    font = Font(color="F8FAFC", bold=True)
    for cell in ws[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")
    for column in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in column)
        ws.column_dimensions[get_column_letter(column[0].column)].width = min(max(max_len + 2, 12), 62)
    ws.freeze_panes = "A2"


def write_xlsx(path: Path, sheets: dict[str, list[dict[str, Any]]]) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for title, rows in sheets.items():
        ws = wb.create_sheet(title[:31])
        if rows:
            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([row.get(header) for header in headers])
        else:
            ws.append(["STATUS"])
            ws.append(["NO_DATA"])
        style_sheet(ws)
    wb.save(path)


def stats(governed: list[dict[str, Any]], benchmark_rows: list[dict[str, Any]], procurement_rows: list[dict[str, Any]], duration: float) -> dict[str, Any]:
    drift_values = [number(row.get("MARKET_DRIFT_SCORE")) for row in governed]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": str(MASTER_INPUT),
        "phase_family": "ELECTRICITE",
        "references": len(governed),
        "benchmark_rows": len(benchmark_rows),
        "procurement_rows": len(procurement_rows),
        "validation_status": count_by(governed, "VALIDATION_STATUS"),
        "confidence_distribution": count_by(governed, "CONFIDENCE_LEVEL"),
        "review_required": len([row for row in governed if row.get("PROCUREMENT_REVIEW_REQUIRED") == "YES"]),
        "average_market_drift_score": round(statistics.mean(drift_values), 2) if drift_values else 0,
        "critical_market_drift": len([value for value in drift_values if value >= 65]),
        "high_confidence_policy": "Strict: supplier, FOB, benchmark, finance, taxonomy and procurement must be verified.",
        "duration_seconds": round(duration, 2),
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "UNKNOWN")
        values[value] = values.get(value, 0) + 1
    return values


def main() -> int:
    start = time.perf_counter()
    print("=== SP2I Procurement Governance V2 ===")
    try:
        master_rows = read_sheet(MASTER_INPUT, "MASTER_REFERENCE")
        governed, benchmark_rows, procurement_rows = build_governance_rows(master_rows)
        low_supplier_rows = [
            row for row in procurement_rows
            if row["SUPPLIER_VERIFIED"] != STATUS_VERIFIED or row["FOB_VERIFIED"] != STATUS_VERIFIED or row["PROCUREMENT_REVIEW_REQUIRED"] == "YES"
        ]
        drift_rows = sorted(benchmark_rows, key=lambda row: number(row.get("MARKET_DRIFT_SCORE")), reverse=True)
        write_xlsx(MASTER_V2, {"MASTER_GOVERNANCE_V2": governed})
        write_xlsx(PROCUREMENT_AUDIT, {"PROCUREMENT_VALIDATION": procurement_rows})
        write_xlsx(BENCHMARK_DRIFT_AUDIT, {"BENCHMARK_DRIFT": benchmark_rows})
        write_xlsx(LOW_CONFIDENCE_SUPPLIERS, {"LOW_CONFIDENCE_SUPPLIERS": low_supplier_rows})
        write_xlsx(MARKET_DRIFT_ANALYSIS, {"MARKET_DRIFT": drift_rows})
        payload = stats(governed, benchmark_rows, procurement_rows, time.perf_counter() - start)
        STATS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("\nLivrables:")
        for path in [MASTER_V2, PROCUREMENT_AUDIT, BENCHMARK_DRIFT_AUDIT, LOW_CONFIDENCE_SUPPLIERS, MARKET_DRIFT_ANALYSIS, STATS_PATH]:
            print(f"- {path.name}")
        return 0
    except Exception:
        print("PROCUREMENT GOVERNANCE V2 FAILED")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
