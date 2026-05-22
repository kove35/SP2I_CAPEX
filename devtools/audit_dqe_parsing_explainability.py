from __future__ import annotations

import json
import re
import time
import traceback
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
DQE_PATH = ROOT / "03_DONNEES_REFERENCE" / "DQE_PROJECT_SP2I.xlsx"
SHEET_NAME = "DQE_CLEAN"

AUDIT_OUT = ROOT / "DQE_PARSING_AUDIT.xlsx"
HEATMAP_OUT = ROOT / "DQE_REJECTION_HEATMAP.xlsx"
STATS_OUT = ROOT / "DQE_PARSING_STATS.json"

VALID_STATUSES = {
    "VALID",
    "WARNING",
    "REVIEW_REQUIRED",
    "IGNORED_TITLE",
    "IGNORED_SUBTOTAL",
    "IGNORED_EMPTY",
    "REJECTED",
}

REASON_MESSAGES = {
    "MISSING_DESIGNATION": "La designation est absente sur cette ligne.",
    "MISSING_QTE": "La quantite est absente sur cette ligne.",
    "MISSING_UNITE": "L'unite est absente sur cette ligne.",
    "INVALID_QTE": "La quantite semble invalide ou non numerique.",
    "INVALID_UNIT": "L'unite n'est pas reconnue.",
    "MERGED_CELL_ERROR": "La ligne contient ou touche une cellule fusionnee qui peut fausser la lecture.",
    "UNKNOWN_FAMILY": "La famille metier n'a pas pu etre identifiee avec suffisamment de confiance.",
    "PARSER_SHIFT_DETECTED": "Le format Excel semble decale ou mal structure.",
    "HEADER_REPEATED": "Une ligne d'en-tete est repetee dans le tableau.",
    "SUBTOTAL_DETECTED": "La ligne correspond a un total ou sous-total.",
    "EMPTY_LINE": "La ligne est vide.",
    "AMBIGUOUS_LINE": "La ligne est ambigue et doit etre revue manuellement.",
    "INVALID_PRICE": "Le prix est absent, nul ou incoherent pour une ligne exploitable.",
    "MULTI_ARTICLE_LINE": "La ligne semble contenir plusieurs articles dans une seule cellule.",
    "LOW_CONFIDENCE_MAPPING": "Le rattachement metier est trop faible pour alimenter les KPI sans revue.",
}

TITLE_PATTERNS = [
    r"^lot\b",
    r"^chapitre\b",
    r"^section\b",
    r"^poste\b",
    r"^generalites\b",
    r"^prescriptions\b",
    r"^batiment\b",
    r"^niveau\b",
]

SUBTOTAL_PATTERNS = [
    r"\bsous[- ]?total\b",
    r"\btotal\b",
    r"\bmontant total\b",
    r"\brecapitulatif\b",
]

COMMENT_PATTERNS = [
    r"\bnote\b",
    r"\bcommentaire\b",
    r"\bvoir plan\b",
    r"\bselon plan\b",
    r"\bcompris toutes sujetions\b",
]

UNIT_ALIASES = {
    "U",
    "UN",
    "UNITE",
    "ENS",
    "ML",
    "M",
    "M2",
    "M3",
    "KG",
    "T",
    "TONNE",
    "FORFAIT",
    "FFT",
    "LOT",
    "H",
    "J",
}

FAMILY_KEYWORDS = {
    "ELECTRICITE": ["electric", "cable", "tgbt", "tableau", "groupe electrogene", "luminaire", "prise", "baes"],
    "HVAC": ["clim", "split", "vrv", "vrf", "ventilation", "extraction", "gaine", "cta"],
    "PLOMBERIE": ["plomberie", "sanitaire", "pvc", "cuivre", "pompe", "eau", "evacuation", "robinet"],
    "MENUISERIE_ALU": ["aluminium", "alu", "vitrage", "chassis", "fenetre", "facade", "garde corps"],
    "MENUISERIE_BOIS": ["bois", "porte bois", "placard", "cuisine"],
    "REVETEMENTS": ["carrelage", "faience", "peinture", "faux plafond", "sol souple"],
    "GROS_OEUVRE": ["beton", "acier", "coffrage", "maconnerie", "gros oeuvre"],
    "VRD": ["vrd", "voirie", "drainage", "terrassement", "reseau"],
    "MEDICAL": ["medical", "laboratoire", "radiologie", "sterilisation", "dentaire"],
    "SECURITE": ["incendie", "videosurveillance", "controle acces", "intrusion"],
}

HEADER_ALIASES = {
    "designation": ["designation", "designations", "libelle", "description", "raw_designation", "designation_normalisee"],
    "qte": ["qte", "quantite", "qty", "quantity"],
    "unite": ["unite", "unit", "u"],
    "price": ["pu", "prix", "prix_unitaire", "pu_estime_local_fcfa", "montant", "total", "prix_total_ht"],
    "lot": ["lot", "famille_lot", "poste"],
    "family": ["famille", "family", "famille_metier"],
    "type_ligne": ["type_ligne", "type", "line_type"],
    "building": ["batiment", "building", "bloc"],
    "level": ["niveau", "level", "etage"],
}


def strip_accents(value: Any) -> str:
    text = "" if value is None else str(value)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize(value: Any) -> str:
    text = strip_accents(value).lower()
    text = re.sub(r"[^a-z0-9%./+ -]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_header(value: Any) -> str:
    return normalize(value).replace(" ", "_")


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        if value != value:
            return None
        return float(value)
    text = str(value).strip().replace("\u202f", "").replace(" ", "")
    text = text.replace(",", ".")
    text = re.sub(r"[^0-9.+-]", "", text)
    if text in {"", ".", "+", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def detect_header(headers: list[str], aliases: list[str]) -> str | None:
    alias_set = set(aliases)
    for header in headers:
        if header in alias_set:
            return header
    for header in headers:
        if any(alias in header for alias in alias_set):
            return header
    return None


def read_rows() -> tuple[list[dict[str, Any]], dict[str, str | None], set[int]]:
    if not DQE_PATH.exists():
        raise FileNotFoundError(f"Fichier DQE introuvable: {DQE_PATH}")
    wb = load_workbook(DQE_PATH, data_only=True)
    if SHEET_NAME not in wb.sheetnames:
        raise ValueError(f"Onglet {SHEET_NAME} introuvable dans {DQE_PATH.name}")
    ws = wb[SHEET_NAME]
    merged_rows: set[int] = set()
    for merged_range in ws.merged_cells.ranges:
        for row_index in range(merged_range.min_row, merged_range.max_row + 1):
            merged_rows.add(row_index)

    raw_rows = list(ws.iter_rows(values_only=True))
    if not raw_rows:
        return [], {}, merged_rows

    header_index = 0
    best_score = -1
    for index, row in enumerate(raw_rows[:15]):
        headers = [normalize_header(cell) for cell in row]
        score = sum(1 for aliases in HEADER_ALIASES.values() if detect_header(headers, aliases))
        if score > best_score:
            header_index = index
            best_score = score

    headers = [normalize_header(cell) or f"col_{index + 1}" for index, cell in enumerate(raw_rows[header_index])]
    fields = {field: detect_header(headers, aliases) for field, aliases in HEADER_ALIASES.items()}
    rows: list[dict[str, Any]] = []
    for source_row, values in enumerate(raw_rows[header_index + 1 :], start=header_index + 2):
        row = {headers[index]: value for index, value in enumerate(values) if index < len(headers)}
        row["_source_row"] = source_row
        row["_sheet"] = SHEET_NAME
        row["_raw_text"] = " | ".join(str(value).strip() for value in values if value not in (None, ""))
        rows.append(row)
    return rows, fields, merged_rows


def value(row: dict[str, Any], field: str, fields: dict[str, str | None]) -> Any:
    key = fields.get(field)
    return row.get(key) if key else None


def detect_family(text: str, explicit: Any = None) -> tuple[str, int]:
    explicit_text = normalize(explicit)
    for family in FAMILY_KEYWORDS:
        if normalize(family) in explicit_text:
            return family, 95
    scores: dict[str, int] = {}
    for family, keywords in FAMILY_KEYWORDS.items():
        scores[family] = sum(1 for keyword in keywords if keyword in text)
    family, score = max(scores.items(), key=lambda item: item[1])
    if score <= 0:
        return "UNKNOWN", 0
    return family, min(95, 45 + score * 18)


def is_repeated_header(text: str) -> bool:
    hits = ["designation", "quantite", "unite", "prix", "montant"]
    return sum(1 for item in hits if item in text) >= 3


def is_title(text: str, qte: float | None, unit: str, price: float | None, type_ligne: str) -> bool:
    if type_ligne == "TITRE_SECTION":
        return True
    if qte is not None or price is not None:
        return False
    if any(re.search(pattern, text) for pattern in TITLE_PATTERNS):
        return True
    words = text.split()
    return 1 <= len(words) <= 8 and not unit and text.upper() == text


def is_subtotal(text: str, type_ligne: str) -> bool:
    return type_ligne == "TOTAL" or any(re.search(pattern, text) for pattern in SUBTOTAL_PATTERNS)


def detect_multi_article(text: str) -> bool:
    separators = ["; ", " / ", " + "]
    has_many_separators = sum(text.count(separator) for separator in separators) >= 2
    has_multiple_units = len(re.findall(r"\b\d+(\.\d+)?\s*(u|ml|m2|m3|kg|ens)\b", text)) >= 2
    return has_many_separators or has_multiple_units


def classify_row(row: dict[str, Any], fields: dict[str, str | None], merged_rows: set[int]) -> dict[str, Any]:
    raw_text = row["_raw_text"]
    text = normalize(raw_text)
    source_row = int(row["_source_row"])
    designation = value(row, "designation", fields)
    qte = number(value(row, "qte", fields))
    unit_raw = value(row, "unite", fields)
    unit = normalize(unit_raw).upper().replace(" ", "")
    price = number(value(row, "price", fields))
    lot = value(row, "lot", fields)
    explicit_family = value(row, "family", fields)
    type_ligne = normalize(value(row, "type_ligne", fields)).upper()
    family, family_confidence = detect_family(f"{text} {normalize(lot)}", explicit_family)

    reasons: list[str] = []
    status = "VALID"
    severity = "OK"
    recoverable = False
    action = "Ligne exploitable pour les calculs."

    if not text:
        status, reasons, severity, action = "IGNORED_EMPTY", ["EMPTY_LINE"], "INFO", "Ignorer cette ligne vide."
    elif is_repeated_header(text):
        status, reasons, severity, recoverable = "WARNING", ["HEADER_REPEATED"], "WARNING", True
        action = "Supprimer l'en-tete repete ou verifier le collage Excel."
    elif is_subtotal(text, type_ligne):
        status, reasons, severity, action = "IGNORED_SUBTOTAL", ["SUBTOTAL_DETECTED"], "INFO", "Ignorer ce total pour eviter un double comptage CAPEX."
    elif is_title(text, qte, unit, price, type_ligne):
        status, reasons, severity, action = "IGNORED_TITLE", ["AMBIGUOUS_LINE"], "INFO", "Conserver comme titre/section, ne pas envoyer aux KPI."
    else:
        if source_row in merged_rows:
            reasons.append("MERGED_CELL_ERROR")
        if not normalize(designation):
            reasons.append("MISSING_DESIGNATION")
        if qte is None:
            reasons.append("MISSING_QTE")
        elif qte <= 0:
            reasons.append("INVALID_QTE")
        if not unit:
            reasons.append("MISSING_UNITE")
        elif unit not in UNIT_ALIASES:
            reasons.append("INVALID_UNIT")
        if price is not None and price < 0:
            reasons.append("INVALID_PRICE")
        if family == "UNKNOWN":
            reasons.append("UNKNOWN_FAMILY")
        elif family_confidence < 60:
            reasons.append("LOW_CONFIDENCE_MAPPING")
        if detect_multi_article(text):
            reasons.append("MULTI_ARTICLE_LINE")
        if any(re.search(pattern, text) for pattern in COMMENT_PATTERNS):
            reasons.append("AMBIGUOUS_LINE")
        if len([cell for key, cell in row.items() if not key.startswith("_") and cell not in (None, "")]) <= 1 and len(text.split()) > 10:
            reasons.append("PARSER_SHIFT_DETECTED")

        blocking = {"MISSING_DESIGNATION", "INVALID_QTE", "PARSER_SHIFT_DETECTED", "MULTI_ARTICLE_LINE"}
        review = {"MISSING_QTE", "MERGED_CELL_ERROR", "UNKNOWN_FAMILY", "AMBIGUOUS_LINE", "LOW_CONFIDENCE_MAPPING"}
        warning = {"MISSING_UNITE", "INVALID_UNIT", "INVALID_PRICE"}
        if any(reason in blocking for reason in reasons):
            status = "REJECTED"
            severity = "ERROR"
            recoverable = True
            action = "Corriger la structure de la ligne avant import; ne pas alimenter les KPI."
        elif any(reason in review for reason in reasons):
            status = "REVIEW_REQUIRED"
            severity = "WARNING"
            recoverable = True
            action = "Faire verifier la ligne par un utilisateur metier avant calcul."
        elif any(reason in warning for reason in reasons):
            status = "WARNING"
            severity = "WARNING"
            recoverable = True
            action = "La ligne peut etre relue; elle ne doit pas declencher une decision automatique."

    if not reasons:
        reasons = ["OK"]

    return {
        "SOURCE_ROW": source_row,
        "SHEET_NAME": row["_sheet"],
        "RAW_TEXT": raw_text,
        "PARSING_STATUS": status,
        "REJECTION_REASON": "|".join(reasons),
        "REJECTION_EXPLANATION": " ".join(REASON_MESSAGES.get(reason, "Ligne exploitable.") for reason in reasons if reason != "OK") or "Ligne exploitable.",
        "GOVERNANCE_SEVERITY": severity,
        "RECOVERABLE": recoverable,
        "RECOMMENDED_ACTION": action,
        "DETECTED_FAMILY": family,
        "FAMILY_CONFIDENCE": family_confidence,
        "DETECTED_UNIT": unit or "",
        "DETECTED_QTE": qte if qte is not None else "",
        "DETECTED_PRICE": price if price is not None else "",
        "LOT": lot or "",
        "BATIMENT": value(row, "building", fields) or "",
        "NIVEAU": value(row, "level", fields) or "",
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(record["PARSING_STATUS"] for record in records)
    ignored = sum(status_counts[status] for status in ["IGNORED_TITLE", "IGNORED_SUBTOTAL", "IGNORED_EMPTY"])
    rejected = status_counts["REJECTED"]
    warnings = status_counts["WARNING"]
    review = status_counts["REVIEW_REQUIRED"]
    total = len(records)
    families = Counter(record["DETECTED_FAMILY"] for record in records if record["PARSING_STATUS"] in {"REJECTED", "WARNING", "REVIEW_REQUIRED"})
    reasons = Counter()
    for record in records:
        for reason in str(record["REJECTION_REASON"]).split("|"):
            if reason != "OK":
                reasons[reason] += 1
    return {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "source_file": str(DQE_PATH),
        "sheet": SHEET_NAME,
        "total_lignes": total,
        "lignes_validees": status_counts["VALID"],
        "warnings": warnings,
        "review_required": review,
        "rejetees": rejected,
        "ignorees": ignored,
        "ignored_title": status_counts["IGNORED_TITLE"],
        "ignored_subtotal": status_counts["IGNORED_SUBTOTAL"],
        "ignored_empty": status_counts["IGNORED_EMPTY"],
        "taux_perte_stricte": round(rejected / total, 4) if total else 0,
        "taux_non_exploitable_kpi": round((rejected + review) / total, 4) if total else 0,
        "familles_impactees": dict(families.most_common()),
        "top_erreurs": dict(reasons.most_common(15)),
        "massive_loss_detected": (rejected + review) / total > 0.20 if total else False,
        "governance_policy": "Strict: rejected/review lines must not feed KPI, ROI, CAPEX or procurement decisions without correction.",
    }


def heatmap_rows(records: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = str(record.get(group_key) or "NON_RENSEIGNE")
        grouped[key].append(record)
    rows = []
    for key, items in grouped.items():
        count = Counter(item["PARSING_STATUS"] for item in items)
        total = len(items)
        rows.append({
            group_key: key,
            "TOTAL": total,
            "VALID": count["VALID"],
            "WARNING": count["WARNING"],
            "REVIEW_REQUIRED": count["REVIEW_REQUIRED"],
            "REJECTED": count["REJECTED"],
            "IGNORED": count["IGNORED_TITLE"] + count["IGNORED_SUBTOTAL"] + count["IGNORED_EMPTY"],
            "TAUX_REJET": round(count["REJECTED"] / total, 4) if total else 0,
        })
    return sorted(rows, key=lambda row: (row["REJECTED"], row["REVIEW_REQUIRED"]), reverse=True)


def write_xlsx(path: Path, sheets: dict[str, list[dict[str, Any]]]) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(sheet_name[:31])
        headers = list(rows[0].keys()) if rows else ["STATUS"]
        ws.append(headers)
        for row in rows or [{"STATUS": "NO_DATA"}]:
            ws.append([row.get(header, "") for header in headers])
        style_sheet(ws)
    wb.save(path)


def style_sheet(ws) -> None:
    header_fill = PatternFill("solid", fgColor="102A43")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            value = str(cell.value or "").upper()
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if value in {"REJECTED", "ERROR"}:
                cell.fill = PatternFill("solid", fgColor="F4CCCC")
            elif value in {"REVIEW_REQUIRED", "WARNING"}:
                cell.fill = PatternFill("solid", fgColor="FCE5CD")
            elif value.startswith("IGNORED"):
                cell.fill = PatternFill("solid", fgColor="D9EAD3")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for column in ws.columns:
        width = min(70, max(12, max(len(str(cell.value or "")) for cell in column) + 2))
        ws.column_dimensions[get_column_letter(column[0].column)].width = width


def main() -> int:
    start = time.perf_counter()
    print("=== SP2I DQE Parsing Explainability Audit ===")
    try:
        rows, fields, merged_rows = read_rows()
        records = [classify_row(row, fields, merged_rows) for row in rows]
        stats = summarize(records)
        write_xlsx(AUDIT_OUT, {"PARSING_AUDIT": records})
        write_xlsx(HEATMAP_OUT, {
            "BY_LOT": heatmap_rows(records, "LOT"),
            "BY_FAMILY": heatmap_rows(records, "DETECTED_FAMILY"),
            "BY_SHEET": heatmap_rows(records, "SHEET_NAME"),
            "BY_ERROR": [{"REJECTION_REASON": key, "COUNT": value} for key, value in stats["top_erreurs"].items()],
            "BY_BUILDING": heatmap_rows(records, "BATIMENT"),
            "BY_LEVEL": heatmap_rows(records, "NIVEAU"),
        })
        stats["duration_seconds"] = round(time.perf_counter() - start, 2)
        STATS_OUT.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        print("\nLivrables:")
        for path in [AUDIT_OUT, HEATMAP_OUT, STATS_OUT]:
            print(f"- {path.name}")
        return 0
    except Exception:
        print("\nERREUR DQE PARSING EXPLAINABILITY")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
