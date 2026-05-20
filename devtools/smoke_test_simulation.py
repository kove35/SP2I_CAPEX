from __future__ import annotations

from _common import CheckResult, import_module, print_result, print_summary, timed_check, title


SAMPLE_LINE = {
    "id_ligne": "DEVTOOLS-001",
    "designation": "Groupe electrogene",
    "famille": "equipement_technique",
    "lot": "Lot DEV",
    "QTE": 1,
    "quantite": 1,
    "prix_total_ht": 100000,
    "prix_fob": 70000,
    "CAPEX_LOCAL": 100000,
    "CAPEX_IMPORT": 76000,
    "CAPEX_OPTIMISE": 76000,
    "ECONOMIE_NETTE": 24000,
    "supplier_moq": 1,
    "quality_score": 88,
    "reliability_score": 82,
    "supplier_risk_score": 20,
    "logistics_risk_score": 20,
    "lead_time_days": 20,
    "project_criticality": "LOW",
}


def test_procurement() -> tuple[bool, str, list[str]]:
    engine_cls = import_module("app.core.procurement_enrichment_engine").ProcurementEnrichmentEngine
    result = engine_cls().enrich_line(dict(SAMPLE_LINE))
    required = ["SOURCING_COVERAGE", "IMPORTABILITY_SCORE", "PROCUREMENT_SCORE", "HIDDEN_SAVINGS_POTENTIAL"]
    missing = [key for key in required if key not in result]
    return not missing, "ProcurementEnrichmentEngine execute", [f"{key}={result.get(key)}" for key in required] + missing


def test_decision() -> tuple[bool, str, list[str]]:
    engine_cls = import_module("app.core.decision_engine_v2").DecisionEngineV2
    line = dict(SAMPLE_LINE, IMPORTABILITY_SCORE=80, PROCUREMENT_MATURITY_SCORE=80)
    decision = engine_cls({"scenario_type": "BASELINE"}).make_decision(line)
    required = ["decision", "final_score", "scenario_type", "reasoning"]
    missing = [key for key in required if key not in decision]
    return not missing, "DecisionEngineV2 execute", [f"{key}={decision.get(key)}" for key in required] + missing


def test_kpi() -> tuple[bool, str, list[str]]:
    engine_cls = import_module("app.core.kpi_engine").KPIEngine
    kpi = engine_cls().compute_procurement_kpi([dict(SAMPLE_LINE, IMPORTABILITY_SCORE=80, PROCUREMENT_SCORE=75)])
    required = ["CAPEX_BRUT", "CAPEX_DECISION", "POTENTIEL_CACHE", "SCORE_PROCUREMENT", "DEPENDANCE_IMPORT"]
    missing = [key for key in required if key not in kpi]
    return not missing, "KPIEngine execute", [f"{key}={kpi.get(key)}" for key in required] + missing


def test_explainability() -> tuple[bool, str, list[str]]:
    engine_cls = import_module("app.core.explainability_engine").ExplainabilityEngine
    line = dict(
        SAMPLE_LINE,
        DECISION_FINALE="IMPORT",
        FINAL_DECISION_SCORE=90,
        IMPORTABILITY_SCORE=80,
        PROCUREMENT_SCORE=60,
        HIDDEN_SAVINGS_POTENTIAL=12,
        SUPPLIER_MATURITY_SCORE=65,
        PROCUREMENT_MATURITY_SCORE=55,
        CONTAINER_STRATEGY="FCL",
        STORAGE_COST=800,
    )
    explanation = engine_cls().explain_line(line)
    required = ["decision", "summary", "procurement", "technical", "financial"]
    missing = [key for key in required if key not in explanation]
    return not missing, "ExplainabilityEngine execute", [f"{key}=OK" for key in required if key in explanation] + missing


def test_audit() -> tuple[bool, str, list[str]]:
    registry_cls = import_module("app.core.parameter_registry_engine").ParameterRegistryEngine
    engine_cls = import_module("app.core.audit_trail_engine").AuditTrailEngine
    audit = engine_cls(registry_cls()).build_line_audit(
        dict(
            SAMPLE_LINE,
            DECISION_FINALE="IMPORT",
            DECISION_TYPE="IMPORT_CONTROLE",
            FINAL_DECISION_SCORE=77,
            DECISION_CONFIDENCE="MEDIUM",
            DECISION_REASON={"savings_score": 80, "risk_score": 20},
        )
    )
    required = ["decision", "decision_type", "scores", "parameters", "line_context", "engine_version"]
    missing = [key for key in required if key not in audit]
    return not missing, "AuditTrailEngine execute", [f"{key}=OK" for key in required if key in audit] + missing


def test_scenario_persistence_class() -> tuple[bool, str, list[str]]:
    engine_cls = import_module("app.core.scenario_persistence_engine").ScenarioPersistenceEngine
    methods = ["persist_scenario", "get_scenario_snapshot", "compare_scenarios", "rollback_scenario"]
    missing = [name for name in methods if not hasattr(engine_cls, name)]
    details = [f"{name}=present" for name in methods if hasattr(engine_cls, name)]
    return not missing, "ScenarioPersistenceEngine inspecte sans ecriture DB", details + missing


def main() -> int:
    title("DEVTOOLS | Smoke test simulation metier")
    results: list[CheckResult] = [
        timed_check("Procurement enrichment", test_procurement),
        timed_check("Decision engine V2", test_decision),
        timed_check("KPI engine", test_kpi),
        timed_check("Explainability engine", test_explainability),
        timed_check("Audit trail engine", test_audit),
        timed_check("Scenario persistence engine", test_scenario_persistence_class),
    ]
    for result in results:
        print_result(result)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

