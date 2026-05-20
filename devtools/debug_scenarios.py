from __future__ import annotations

from _common import CORE_DIR, CheckResult, import_module, inspect_classes, print_result, print_summary, timed_check, title


def detect_scenario_engines() -> tuple[bool, str, list[str]]:
    details: list[str] = []
    for path in sorted(CORE_DIR.glob("scenario*_engine.py")):
        module = import_module(f"app.core.{path.stem}")
        classes = inspect_classes(module)
        details.append(f"{path.name}: {', '.join(cls.__name__ for cls in classes) or 'aucune classe'}")
    return True, f"{len(details)} module(s) scenario detecte(s)", details


def inspect_persistence_contract() -> tuple[bool, str, list[str]]:
    engine_cls = import_module("app.core.scenario_persistence_engine").ScenarioPersistenceEngine
    expected = ["persist_scenario", "get_scenario_snapshot", "compare_scenarios", "rollback_scenario"]
    missing = [name for name in expected if not hasattr(engine_cls, name)]
    return not missing, "contrat ScenarioPersistenceEngine inspecte", [f"{name}=OK" for name in expected if hasattr(engine_cls, name)] + missing


def main() -> int:
    title("DEVTOOLS | Debug scenarios")
    results: list[CheckResult] = [
        timed_check("Detection engines scenarios", detect_scenario_engines),
        timed_check("Contrat persistence", inspect_persistence_contract),
    ]
    for result in results:
        print_result(result)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

