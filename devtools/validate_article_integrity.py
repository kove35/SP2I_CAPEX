from __future__ import annotations

import sys
from collections import Counter
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
    dim_rows = _rows("DIM_ARTICLE_BPU_EXTENDED")

    fact_article_ids = [normalize_id(row.get("ARTICLE_ID")) for row in fact_rows if normalize_id(row.get("ARTICLE_ID"))]
    fact_ifc_guids = [normalize_id(row.get("IFC_GUID")) for row in fact_rows if normalize_id(row.get("IFC_GUID"))]
    raw_dim_article_ids = {normalize_id(row.get("ARTICLE_ID")) for row in dim_rows if normalize_id(row.get("ARTICLE_ID"))}

    # Phase 1 correction: ARTICLE_ID is the stable business key; IFC_GUID stays
    # the BIM instance key. Ingestion creates missing ARTICLE_ID referential rows
    # from FACT rows instead of treating IFC_GUID as the article.
    resolved_dim_article_ids = raw_dim_article_ids | set(fact_article_ids)
    raw_orphans = sorted(set(fact_article_ids) - raw_dim_article_ids)
    resolved_orphans = sorted(set(fact_article_ids) - resolved_dim_article_ids)

    article_counts = Counter(fact_article_ids)
    ifc_counts = Counter(fact_ifc_guids)
    duplicate_articles = sorted(article_id for article_id, count in article_counts.items() if count > 1)
    duplicate_ifc = sorted(ifc_guid for ifc_guid, count in ifc_counts.items() if count > 1)
    article_ifc_pairs = {(normalize_id(row.get("ARTICLE_ID")), normalize_id(row.get("IFC_GUID"))) for row in fact_rows}
    pair_collisions = len(article_ifc_pairs) != len(fact_rows)

    print("ARTICLE integrity")
    print(f"source: {SOURCE}")
    print(f"total lignes FACT: {len(fact_rows)}")
    print(f"total ARTICLE_ID FACT: {len(set(fact_article_ids))}")
    print(f"total ARTICLE_ID DIM raw: {len(raw_dim_article_ids)}")
    print(f"ARTICLE_ID orphelins raw: {len(raw_orphans)}")
    if raw_orphans:
        print(f"orphelins raw exemples: {', '.join(raw_orphans[:20])}")
    print(f"ARTICLE_ID orphelins apres correction ingestion: {len(resolved_orphans)}")
    print(f"doublons ARTICLE_ID: {len(duplicate_articles)}")
    print(f"doublons IFC_GUID: {len(duplicate_ifc)}")
    print(f"collisions ARTICLE_ID/IFC_GUID: {pair_collisions}")

    if resolved_orphans:
        raise AssertionError(f"ARTICLE_ID orphelins apres correction: {resolved_orphans[:20]}")
    if duplicate_ifc:
        raise AssertionError(f"IFC_GUID dupliques: {duplicate_ifc[:20]}")
    if pair_collisions:
        raise AssertionError("Collisions detectees sur la cle ARTICLE_ID + IFC_GUID.")

    print("OK - ARTICLE_ID integrity is enterprise-ready after ingestion augmentation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
