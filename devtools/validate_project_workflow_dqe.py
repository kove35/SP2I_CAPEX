from __future__ import annotations

import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.projects.models import Project
from app.projects.routes import compute_project_workflow_status

EXPECTED_DQE_STATUSES = {
    "NOT_IMPORTED",
    "UPLOADED",
    "ANALYZED",
    "CERTIFIED",
    "CERTIFIED_WITH_WARNINGS",
    "REVIEW_REQUIRED",
    "REJECTED",
    "SYNCED",
}


def section(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def main() -> int:
    started = time.perf_counter()
    section("DEVTOOLS | Validation workflow projet DQE")

    try:
        configured_project = Project(
            id=1,
            name="Projet test DQE",
            client_name="Client test",
            city="Pointe-Noire",
            country="Congo-Brazzaville",
            currency="FCFA",
            project_type="Etablissement de sante",
            project_manager="Responsable test",
            setup_status="CONFIGURED",
            setup_completed_at=datetime.now(),
            owner_id=1,
            status="ACTIVE",
        )

        unconfigured_project = Project(
            id=2,
            name="",
            client_name="",
            city="",
            country="",
            currency="",
            project_type="",
            project_manager="",
            setup_status="CONFIG_REQUIRED",
            setup_completed_at=None,
            owner_id=1,
            status="ACTIVE",
        )

        configured_workflow = compute_project_workflow_status(configured_project, None)
        unconfigured_workflow = compute_project_workflow_status(unconfigured_project, None)

        print(f"[INFO] Projet non configure: status workflow = {unconfigured_workflow.status}")
        print(f"[INFO] Projet configure: status workflow = {configured_workflow.status}")
        print(f"[INFO] DQE status: {configured_workflow.dqe.status}")
        print(f"[INFO] Primary action: {configured_workflow.primary_action}")

        if unconfigured_workflow.status != "CONFIG_REQUIRED":
            print("[FAIL] Le projet non configure doit rester en CONFIG_REQUIRED.")
            return 1

        if configured_workflow.dqe.status not in EXPECTED_DQE_STATUSES:
            print(f"[FAIL] Statut DQE inattendu: {configured_workflow.dqe.status}")
            return 1

        if not getattr(configured_workflow.primary_action, "label", None):
            print("[FAIL] Aucune action principale retournee pour le workflow.")
            return 1

        elapsed = round((time.perf_counter() - started) * 1000, 1)
        print(f"\nResume final: OK ({elapsed} ms)")
        return 0
    except Exception:
        print("[FAIL] Validation workflow DQE impossible.")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
