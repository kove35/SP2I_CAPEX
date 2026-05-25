from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.governance.dqe_issue_catalog import ISSUE_DEFINITIONS, validate_issue_catalog  # noqa: E402


def main() -> int:
    print("DEVTOOLS | Validation DQE issue catalog")
    errors = validate_issue_catalog()
    if errors:
        print("[FAIL] Catalogue incomplet")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"[OK] {len(ISSUE_DEFINITIONS)} anomalies documentees")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
