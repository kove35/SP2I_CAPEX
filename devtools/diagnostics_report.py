from __future__ import annotations

import platform

from fastapi.routing import APIRoute

from _common import (
    CORE_DIR,
    ROOT,
    CheckResult,
    discover_modules,
    import_module,
    inspect_classes,
    print_result,
    print_summary,
    section,
    timed_check,
    title,
)
from validate_imports import check_cycles, check_imports, check_init_files
from validate_routes import check_collisions, check_pydantic_models, load_app


def architecture_report() -> tuple[bool, str, list[str]]:
    details = [
        f"root={ROOT}",
        f"python={platform.python_version()}",
        f"platform={platform.platform()}",
        f"modules_app={len(discover_modules())}",
    ]
    for folder in ["07_API_BACKEND", "tests", "devtools"]:
        details.append(f"{folder}={'present' if (ROOT / folder).exists() else 'missing'}")
    return True, "architecture detectee", details


def routes_report() -> tuple[bool, str, list[str]]:
    app = load_app()
    routes = [route for route in app.routes if isinstance(route, APIRoute)]
    details = [f"{','.join(sorted(route.methods or [])):10} {route.path}" for route in routes]
    return True, f"{len(routes)} route(s) FastAPI", details


def engines_report() -> tuple[bool, str, list[str]]:
    details: list[str] = []
    for path in sorted(CORE_DIR.glob("*_engine.py")):
        module = import_module(f"app.core.{path.stem}")
        classes = inspect_classes(module)
        details.append(f"{path.stem}: {', '.join(cls.__name__ for cls in classes) or 'aucune classe'}")
    return True, f"{len(details)} module(s) engine", details


def dependencies_report() -> tuple[bool, str, list[str]]:
    modules = ["fastapi", "pydantic", "sqlalchemy", "pandas", "numpy"]
    details = []
    for module_name in modules:
        module = import_module(module_name)
        details.append(f"{module_name}={getattr(module, '__version__', 'version inconnue')}")
    return True, "dependances critiques importables", details


def recommendations(results: list[CheckResult]) -> None:
    section("Warnings et recommandations")
    if all(result.ok for result in results):
        print("[OK] Aucun blocage critique detecte.")
    else:
        for result in results:
            if not result.ok:
                print(f"[ACTION] Corriger: {result.name} -> {result.message}")
    print("[INFO] Continuer a lancer les scripts via .venv\\Scripts\\python.exe devtools\\<script>.py")
    print("[INFO] Eviter absolument python.exe -c avec du code multi-lignes sous PowerShell.")


def main() -> int:
    title("DEVTOOLS | Rapport diagnostics global")
    results: list[CheckResult] = [
        timed_check("Architecture detectee", architecture_report),
        timed_check("Routes FastAPI", routes_report),
        timed_check("Engines detectes", engines_report),
        timed_check("Dependances detectees", dependencies_report),
        timed_check("Imports backend", check_imports),
        timed_check("Circular imports", check_cycles),
        timed_check("__init__.py", check_init_files),
        timed_check("Collisions routes", check_collisions),
        timed_check("Modeles Pydantic", check_pydantic_models),
    ]
    for result in results:
        print_result(result, verbose=True)
    recommendations(results)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())
