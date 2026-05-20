from __future__ import annotations

import py_compile

from _common import (
    APP_DIR,
    CheckResult,
    discover_modules,
    find_cycles,
    import_all_modules,
    local_import_graph,
    missing_init_files,
    print_result,
    print_summary,
    python_files,
    timed_check,
    title,
)


def check_syntax() -> tuple[bool, str, list[str]]:
    errors: list[str] = []
    files = python_files(APP_DIR)
    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{path}: {exc.msg}")
    if errors:
        return False, f"{len(errors)} fichier(s) avec erreur de syntaxe", errors
    return True, f"{len(files)} fichier(s) Python compilent", []


def check_imports() -> tuple[bool, str, list[str]]:
    imported, errors = import_all_modules(APP_DIR)
    details = [f"Import OK: {name}" for name in imported]
    if errors:
        return False, f"{len(errors)} module(s) cassé(s)", [f"{name}\n{error}" for name, error in errors] + details
    return True, f"{len(imported)} module(s) importables", details


def check_cycles() -> tuple[bool, str, list[str]]:
    graph = local_import_graph(APP_DIR)
    cycles = find_cycles(graph)
    details = [" -> ".join(cycle) for cycle in cycles]
    if cycles:
        return False, f"{len(cycles)} circular import(s) potentiel(s)", details
    return True, "aucun cycle app.* detecté par analyse statique", [f"{len(graph)} module(s) analyses"]


def check_init_files() -> tuple[bool, str, list[str]]:
    missing = missing_init_files(APP_DIR)
    if missing:
        return False, f"{len(missing)} dossier(s) sans __init__.py", [str(path) for path in missing]
    return True, "tous les packages backend ont un __init__.py", []


def main() -> int:
    title("DEVTOOLS | Validation imports backend")
    results: list[CheckResult] = [
        timed_check("Syntaxe Python", check_syntax),
        timed_check("Imports runtime", check_imports),
        timed_check("Circular imports", check_cycles),
        timed_check("__init__.py", check_init_files),
    ]
    for result in results:
        print_result(result, verbose=not result.ok)
    print(f"\nModules detectes: {len(discover_modules(APP_DIR))}")
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())

