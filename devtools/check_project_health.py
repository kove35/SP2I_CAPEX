from __future__ import annotations

from _common import CheckResult, print_result, print_summary, score_from_results, timed_check, title
from debug_procurement import debug_procurement_engine
from debug_scenarios import inspect_persistence_contract
from smoke_test_simulation import test_audit, test_decision, test_explainability, test_kpi
from validate_imports import check_imports
from validate_powerbi_payloads import check_powerbi_routes
from validate_routes import check_routes


def main() -> int:
    title("DEVTOOLS | Health check projet SP2I CAPEX")
    results: list[CheckResult] = [
        timed_check("Statut imports", check_imports),
        timed_check("Statut routes", check_routes),
        timed_check("Statut KPI", test_kpi),
        timed_check("Statut scenarios", inspect_persistence_contract),
        timed_check("Statut procurement", debug_procurement_engine),
        timed_check("Statut explainability", test_explainability),
        timed_check("Statut auditability", test_audit),
        timed_check("Statut Power BI readiness", check_powerbi_routes),
        timed_check("Statut DecisionEngineV2", test_decision),
    ]
    for result in results:
        print_result(result, verbose=not result.ok)
    print(f"\nHealth score global: {score_from_results(results)}/100")
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

