from __future__ import annotations

import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
SOURCE = ROOT / "03_DONNEES_REFERENCE" / "SP2I_BIM_DQE_MASTER_V4_ENTERPRISE.xlsx"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.models import FactMetre  # noqa: E402
from app.services.service_ai_mapping import ServiceAIMapping  # noqa: E402
from app.utils.id_normalizer import normalize_id  # noqa: E402


EXPECTED_FACT_COLUMNS = {
    "projet_id",
    "batiment_id",
    "niveau_id",
    "appartement_id",
    "piece_id",
    "lot_id",
    "sous_lot_id",
    "article_id",
    "ifc_guid",
    "bim_object",
    "quantite",
    "pu_local",
    "pu_import",
    "montant_import",
    "capex_local",
    "capex_import",
    "decision",
    "fournisseur",
    "execution_status",
    "workflow_status",
    "risque",
    "eta",
    "bim_maturity",
}


def _upsert_key(line: dict) -> tuple[str, str, str, str, str]:
    return (
        normalize_id(line.get("article_id") or line.get("id_ligne")),
        normalize_id(line.get("ifc_guid")),
        normalize_id(line.get("niveau_code") or line.get("niveau")),
        normalize_id(line.get("appartement_code") or line.get("appart")),
        normalize_id(line.get("piece_code") or line.get("piece")),
    )


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    started = time.perf_counter()
    service = ServiceAIMapping()
    lines, audit = service.extraire_lignes_normalisees(SOURCE.read_bytes(), SOURCE.name)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    model_columns = set(FactMetre.__table__.columns.keys())
    missing_columns = sorted(EXPECTED_FACT_COLUMNS - model_columns)
    keys = [_upsert_key(line) for line in lines]
    duplicate_keys = len(keys) - len(set(keys))
    governance = (audit.get("ai_confidence") or {}).get("governance_quality") or {}
    bim_maturity = audit.get("bim_maturity") or {}

    print("Enterprise PostgreSQL ingestion validation")
    print(f"source: {SOURCE}")
    print(f"normalized_lines_count: {len(lines)}")
    print(f"parse_normalize_ms: {elapsed_ms}")
    print(f"duplicate_upsert_keys: {duplicate_keys}")
    print(f"missing_fact_model_columns: {missing_columns}")
    print(f"trust_score: {(audit.get('ai_confidence') or {}).get('trust_score')}")
    print(f"certification_status: {'CERTIFIED' if int(governance.get('blocking_loss_rows') or 0) == 0 and int(governance.get('review_required_rows') or 0) == 0 else 'REVIEW_REQUIRED'}")
    print(f"bim_maturity_final: {bim_maturity.get('maturity')}")

    if len(lines) < 290:
        raise AssertionError(f"Expected at least 290 normalized enterprise lines, got {len(lines)}")
    if missing_columns:
        raise AssertionError(f"FactMetre model missing expected columns: {missing_columns}")
    if duplicate_keys:
        raise AssertionError(f"Duplicate composite upsert keys detected: {duplicate_keys}")
    if bim_maturity.get("maturity") != "BIM_READY":
        raise AssertionError(f"Expected BIM_READY, got {bim_maturity.get('maturity')}")

    print("OK - enterprise ingestion contract is ready for PostgreSQL upsert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
