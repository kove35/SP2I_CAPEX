from __future__ import annotations

from collections import defaultdict
import sys

from fastapi.routing import APIRoute
from pydantic import BaseModel

from _common import CheckResult, import_module, print_result, print_summary, timed_check, title


def load_app():
    try:
        module = import_module("app.main")
        return module.app
    except ImportError:
        for name in list(sys.modules):
            if name == "app.main" or name == "app.repositories" or name.startswith("app.repositories."):
                sys.modules.pop(name, None)
        import_module("app.repositories.repository_simulation")
        module = import_module("app.main")
        return module.app


def check_fastapi_app() -> tuple[bool, str, list[str]]:
    app = load_app()
    return True, f"FastAPI app chargee: {app.title}", [f"version={app.version}", f"routes={len(app.routes)}"]


def check_routes() -> tuple[bool, str, list[str]]:
    app = load_app()
    routes = [route for route in app.routes if isinstance(route, APIRoute)]
    details = [f"{','.join(sorted(route.methods or [])):10} {route.path} -> {route.name}" for route in routes]
    if not routes:
        return False, "aucune route APIRoute detectee", []
    return True, f"{len(routes)} endpoint(s) FastAPI detecte(s)", details


def check_collisions() -> tuple[bool, str, list[str]]:
    app = load_app()
    collisions: dict[tuple[str, str], list[str]] = defaultdict(list)
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or []:
            collisions[(method, route.path)].append(route.name)
    duplicates = {key: names for key, names in collisions.items() if len(names) > 1}
    details = [f"{method} {path}: {', '.join(names)}" for (method, path), names in duplicates.items()]
    if duplicates:
        return False, f"{len(duplicates)} collision(s) route/methode", details
    return True, "aucune collision route/methode", []


def check_pydantic_models() -> tuple[bool, str, list[str]]:
    app = load_app()
    details: list[str] = []
    errors: list[str] = []
    count = 0
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        dependant = route.dependant
        body_params = list(getattr(dependant, "body_params", []) or [])
        for param in body_params:
            annotation = getattr(param, "type_", None)
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                count += 1
                try:
                    annotation.model_json_schema()
                    details.append(f"{route.path}: {annotation.__name__}")
                except Exception as exc:
                    errors.append(f"{route.path}: {annotation.__name__}: {exc}")
    if errors:
        return False, f"{len(errors)} modele(s) Pydantic invalide(s)", errors
    return True, f"{count} modele(s) Pydantic body valide(s)", details


def main() -> int:
    title("DEVTOOLS | Validation routes FastAPI")
    results: list[CheckResult] = [
        timed_check("Chargement app FastAPI", check_fastapi_app),
        timed_check("Detection endpoints", check_routes),
        timed_check("Collisions endpoints", check_collisions),
        timed_check("Modeles Pydantic", check_pydantic_models),
    ]
    for result in results:
        print_result(result, verbose=True)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())
