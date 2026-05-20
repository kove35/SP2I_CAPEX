from __future__ import annotations

from smoke_test_simulation import SAMPLE_LINE
from _common import CheckResult, import_module, print_result, print_summary, timed_check, title


def debug_kpi() -> tuple[bool, str, list[str]]:
    engine = import_module("app.core.kpi_engine").KPIEngine()
    lines = [
        dict(SAMPLE_LINE, CAPEX_LOCAL=100000, CAPEX_IMPORT=76000, CAPEX_OPTIMISE=76000, PROCUREMENT_SCORE=75, IMPORTABILITY_SCORE=80),
        dict(SAMPLE_LINE, id_ligne="DEVTOOLS-002", CAPEX_LOCAL=50000, CAPEX_IMPORT=52000, CAPEX_OPTIMISE=50000, PROCUREMENT_SCORE=40, IMPORTABILITY_SCORE=35),
    ]
    kpi = engine.compute_procurement_kpi(lines)
    required = ["CAPEX_BRUT", "CAPEX_DECISION", "POTENTIEL_CACHE", "SCORE_PROCUREMENT", "DEPENDANCE_IMPORT"]
    missing = [key for key in required if key not in kpi]
    return not missing, "diagnostic KPI termine", [f"{key}={kpi.get(key)}" for key in sorted(kpi)]


def main() -> int:
    title("DEVTOOLS | Debug KPI engine")
    results: list[CheckResult] = [timed_check("KPIEngine", debug_kpi)]
    for result in results:
        print_result(result)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

