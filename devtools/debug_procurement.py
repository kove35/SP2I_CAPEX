from __future__ import annotations

from smoke_test_simulation import SAMPLE_LINE
from _common import CheckResult, import_module, print_result, print_summary, timed_check, title


def debug_procurement_engine() -> tuple[bool, str, list[str]]:
    engine = import_module("app.core.procurement_enrichment_engine").ProcurementEnrichmentEngine()
    result = engine.enrich_line(dict(SAMPLE_LINE))
    keys = [
        "SOURCING_COVERAGE",
        "SUPPLIER_MATURITY_SCORE",
        "PROCUREMENT_MATURITY_SCORE",
        "IMPORTABILITY_SCORE",
        "PROCUREMENT_SCORE",
        "HIDDEN_SAVINGS_POTENTIAL",
        "PROCUREMENT_ANALYSIS",
    ]
    missing = [key for key in keys if key not in result]
    return not missing, "diagnostic procurement termine", [f"{key}={result.get(key)}" for key in keys]


def main() -> int:
    title("DEVTOOLS | Debug procurement")
    results: list[CheckResult] = [timed_check("ProcurementEnrichmentEngine", debug_procurement_engine)]
    for result in results:
        print_result(result)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

