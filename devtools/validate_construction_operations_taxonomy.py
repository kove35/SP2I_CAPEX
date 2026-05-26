from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.construction.taxonomy import LOTS_PRINCIPAUX, REMAINING_WORK_STATUSES, SOUS_LOTS_METIER, validate_taxonomy
from app.models import FactMetre


def main() -> None:
    errors = validate_taxonomy()
    if errors:
        raise AssertionError("; ".join(errors))

    required_columns = {
        "projet_id",
        "batiment",
        "niveau",
        "appart",
        "piece",
        "type_zone",
        "altitude",
        "phase_chantier",
        "execution_status",
        "workflow_status",
        "eta",
        "risque",
        "fournisseur",
        "import_local",
        "bim_object_id",
        "ifc_guid",
    }
    model_columns = set(FactMetre.__table__.columns.keys())
    missing = sorted(required_columns - model_columns)
    if missing:
        raise AssertionError(f"FactMetre missing construction operations columns: {missing}")

    if len(LOTS_PRINCIPAUX) < 10 or len(SOUS_LOTS_METIER) < 10:
        raise AssertionError("Construction taxonomy is too small for enterprise bootstrap")
    if "A_EXECUTER" not in REMAINING_WORK_STATUSES or "EXPLOITE" not in REMAINING_WORK_STATUSES:
        raise AssertionError("Remaining works statuses are incomplete")

    print("OK - construction operations taxonomy and FactMetre extensions are valid.")


if __name__ == "__main__":
    main()
