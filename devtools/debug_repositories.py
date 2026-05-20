from __future__ import annotations

from _common import (
    REPOSITORIES_DIR,
    CheckResult,
    import_module,
    inspect_classes,
    print_result,
    print_summary,
    section,
    timed_check,
    title,
)


def check_repository_package() -> tuple[bool, str, list[str]]:
    module = import_module("app.repositories")
    exported = getattr(module, "__all__", [])
    details = [f"Exports __all__: {', '.join(exported) if exported else 'aucun'}"]
    return True, "package app.repositories importable", details


def check_repository_modules() -> tuple[bool, str, list[str]]:
    details: list[str] = []
    errors: list[str] = []
    for path in sorted(REPOSITORIES_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module_name = f"app.repositories.{path.stem}"
        try:
            module = import_module(module_name)
            classes = inspect_classes(module, suffix=None)
            repo_classes = [cls.__name__ for cls in classes if "Repository" in cls.__name__]
            details.append(f"{module_name}: {', '.join(repo_classes) if repo_classes else 'aucune classe Repository'}")
        except Exception as exc:
            errors.append(f"{module_name}: {exc}")
    if errors:
        return False, f"{len(errors)} repository module(s) cassé(s)", errors + details
    return True, "tous les repositories sont importables", details


def check_repository_constructors() -> tuple[bool, str, list[str]]:
    details: list[str] = []
    for path in sorted(REPOSITORIES_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module = import_module(f"app.repositories.{path.stem}")
        for cls in inspect_classes(module):
            if "Repository" in cls.__name__:
                details.append(f"{cls.__module__}.{cls.__name__}: constructeur détecté")
    return True, f"{len(details)} classe(s) repository détectée(s)", details


def main() -> int:
    title("DEVTOOLS | Debug repositories")
    results: list[CheckResult] = [
        timed_check("Import package repositories", check_repository_package),
        timed_check("Import modules repositories", check_repository_modules),
        timed_check("Detection classes repositories", check_repository_constructors),
    ]
    section("Resultats detailles")
    for result in results:
        print_result(result)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

