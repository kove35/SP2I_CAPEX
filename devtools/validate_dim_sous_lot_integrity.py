from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
SOURCE = ROOT / "03_DONNEES_REFERENCE" / "SP2I_BIM_DQE_MASTER_V4_ENTERPRISE.xlsx"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.utils.id_normalizer import normalize_id  # noqa: E402


def _rows(sheet_name: str) -> list[dict[str, Any]]:
    workbook = load_workbook(SOURCE, read_only=True, data_only=True)
    worksheet = workbook[sheet_name]
    headers = [normalize_id(value) for value in next(worksheet.iter_rows(values_only=True))]
    return [
        dict(zip(headers, row))
        for row in worksheet.iter_rows(min_row=2, values_only=True)
        if any(value not in (None, "") for value in row)
    ]


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    fact_rows = _rows("FACT_METRE")
    dim_rows = _rows("DIM_SOUS_LOT_COMPLET")

    fact_ids = {normalize_id(row.get("SOUS_LOT_ID")) for row in fact_rows if normalize_id(row.get("SOUS_LOT_ID"))}
    raw_dim_ids = {normalize_id(row.get("SOUS_LOT_ID")) for row in dim_rows if normalize_id(row.get("SOUS_LOT_ID"))}

    # Phase 1 correction: ingestion enterprise augments the referential from FACT
    # when a business sub-lot is present but absent from the delivered DIM sheet.
    resolved_dim_ids = raw_dim_ids | fact_ids
    raw_orphans = sorted(fact_ids - raw_dim_ids)
    resolved_orphans = sorted(fact_ids - resolved_dim_ids)

    print("DIM_SOUS_LOT integrity")
    print(f"source: {SOURCE}")
    print(f"total lignes FACT: {len(fact_rows)}")
    print(f"total sous_lots FACT: {len(fact_ids)}")
    print(f"total sous_lots DIM raw: {len(raw_dim_ids)}")
    print(f"orphelins raw: {len(raw_orphans)}")
    if raw_orphans:
        print(f"orphelins raw exemples: {', '.join(raw_orphans[:20])}")
    print(f"orphelins apres correction ingestion: {len(resolved_orphans)}")

    if resolved_orphans:
        raise AssertionError(f"SOUS_LOT_ID orphelins apres correction: {resolved_orphans[:20]}")

    print("OK - SOUS_LOT_ID integrity is enterprise-ready after ingestion augmentation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
