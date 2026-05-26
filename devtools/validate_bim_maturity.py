from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.bim.maturity import (  # noqa: E402
    BIM_MATURITY_LITE,
    BIM_MATURITY_NON_BIM,
    BIM_MATURITY_READY,
    detect_bim_maturity_from_columns,
    enrich_bim_maturity_with_lines,
)


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> int:
    classic = detect_bim_maturity_from_columns(["LOT", "DESIGNATION", "U", "QTE", "PU_LOCAL"])
    assert_equal(classic["maturity"], BIM_MATURITY_NON_BIM, "classic DQE maturity")

    lite = detect_bim_maturity_from_columns(["BATIMENT", "NIVEAU", "PIECE", "LOT", "DESIGNATION", "QTE"])
    assert_equal(lite["maturity"], BIM_MATURITY_LITE, "BIM-lite DQE maturity")
    if "CAPEX_PAR_NIVEAU" not in lite["capabilities"]:
        raise AssertionError("BIM-lite capabilities should include CAPEX_PAR_NIVEAU")

    ready = detect_bim_maturity_from_columns(["IFC_GUID", "BIM_OBJECT_ID", "TYPE_OBJET", "DESIGNATION", "QTE"])
    assert_equal(ready["maturity"], BIM_MATURITY_READY, "BIM-ready DQE maturity")
    if "IFC_LINK_READY" not in ready["capabilities"]:
        raise AssertionError("BIM-ready capabilities should include IFC_LINK_READY")

    enriched = enrich_bim_maturity_with_lines(
        lite,
        [
            {"batiment": "A", "niveau": "RDC", "piece": "101"},
            {"batiment": "A", "niveau": "R+1", "piece": ""},
        ],
    )
    assert_equal(enriched["spatialized_lines_count"], 2, "spatialized line count")

    print("BIM maturity detector: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
