from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.decision_engine_v2 import DecisionEngineV2
from app.services.service_simulation import ServiceSimulation


def main() -> None:
    service = ServiceSimulation()
    kpi = {"procurement": {"LIGNES_IMPORTABLES": 24}}
    lines = [
        {"DECISION_FINALE": "IMPORT"},
        {"DECISION_FINALE": "LOCAL"},
        {"DECISION_FINALE": "HYBRIDE"},
    ]
    service._enrichir_kpi_lignes(kpi, lignes_entree=[{}, {}, {}], lignes_normalisees=[{}, {}, {}], lignes_calculees=lines)
    assert kpi["lignes_dqe"] == 3
    assert kpi["lignes_simulees"] == 3
    assert kpi["lignes_importables"] == 24
    assert kpi["lignes_retenues"] == 1
    assert kpi["lignes_arbitrees"] == 3

    decision = DecisionEngineV2({"scenario_type": "BASELINE"}).enrich_line(
        {
            "CAPEX_LOCAL": 100,
            "CAPEX_IMPORT": 95,
            "ECONOMIE_NETTE": 5,
            "RISK_SCORE": 50,
            "LEAD_TIME_SCORE": 50,
            "CRITICALITY_SCORE": 50,
            "IMPORTABILITY_SCORE": 50,
            "PROCUREMENT_MATURITY_SCORE": 50,
        }
    )
    assert decision["DECISION_FINALE"] in {"IMPORT", "LOCAL", "HYBRIDE"}
    print("[OK] Procurement simulation KPI and enterprise statuses")


if __name__ == "__main__":
    main()
