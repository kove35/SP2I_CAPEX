from __future__ import annotations

import ast
import importlib
import inspect
import os
import pkgutil
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
APP_DIR = BACKEND / "app"
ROUTES_DIR = APP_DIR / "routes"
CORE_DIR = APP_DIR / "core"
REPOSITORIES_DIR = APP_DIR / "repositories"


def configure_paths() -> None:
    for path in (str(ROOT), str(BACKEND)):
        if path not in sys.path:
            sys.path.insert(0, path)


def safe_text(value: Any) -> str:
    text = str(value)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def line(char: str = "-", width: int = 88) -> None:
    print(char * width)


def title(name: str) -> None:
    print()
    line("=")
    print(safe_text(name))
    line("=")


def section(name: str) -> None:
    print()
    print(safe_text(name))
    line("-")


def status(level: str, message: str) -> None:
    labels = {
        "ok": "[OK]",
        "warn": "[WARN]",
        "error": "[ERROR]",
        "info": "[INFO]",
        "skip": "[SKIP]",
    }
    print(safe_text(f"{labels.get(level, '[INFO]')} {message}"))


def format_exception(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str = ""
    details: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    error: str | None = None


def timed_check(name: str, func: Callable[[], tuple[bool, str, list[str]]]) -> CheckResult:
    start = time.perf_counter()
    try:
        ok, message, details = func()
        return CheckResult(
            name=name,
            ok=ok,
            message=message,
            details=details,
            duration_ms=(time.perf_counter() - start) * 1000,
        )
    except Exception as exc:
        return CheckResult(
            name=name,
            ok=False,
            message=str(exc),
            duration_ms=(time.perf_counter() - start) * 1000,
            error=format_exception(exc),
        )


def print_result(result: CheckResult, verbose: bool = True) -> None:
    level = "ok" if result.ok else "error"
    status(level, f"{result.name}: {result.message} ({result.duration_ms:.1f} ms)")
    if verbose:
        for detail in result.details:
            print(f"  - {safe_text(detail)}")
    if result.error:
        print(safe_text(result.error))


def print_summary(results: list[CheckResult]) -> int:
    section("Resume final")
    total = len(results)
    failed = [result for result in results if not result.ok]
    for result in results:
        marker = "OK" if result.ok else "FAIL"
        print(f"{marker:5} {result.name} ({result.duration_ms:.1f} ms)")
    print()
    print(f"Checks: {total} | OK: {total - len(failed)} | FAIL: {len(failed)}")
    return 1 if failed else 0


def import_module(module_name: str) -> ModuleType:
    configure_paths()
    return importlib.import_module(module_name)


def module_name_from_path(path: Path) -> str:
    relative = path.relative_to(BACKEND).with_suffix("")
    return ".".join(relative.parts)


def python_files(base: Path = APP_DIR) -> list[Path]:
    return sorted(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)


def discover_modules(base: Path = APP_DIR) -> list[str]:
    return [module_name_from_path(path) for path in python_files(base)]


def import_all_modules(base: Path = APP_DIR) -> tuple[list[str], list[tuple[str, str]]]:
    imported: list[str] = []
    errors: list[tuple[str, str]] = []
    for module_name in discover_modules(base):
        try:
            import_module(module_name)
            imported.append(module_name)
        except Exception as exc:
            errors.append((module_name, format_exception(exc)))
    return imported, errors


def parse_imports(path: Path, current_module: str | None = None) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            base = node.module
            for alias in node.names:
                if alias.name == "*":
                    modules.add(base)
                else:
                    modules.add(f"{base}.{alias.name}")
            modules.add(base)
    if current_module:
        modules.discard(current_module)
    return modules


def local_import_graph(base: Path = APP_DIR) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    module_names = set(discover_modules(base))
    for path in python_files(base):
        module_name = module_name_from_path(path)
        graph[module_name] = set()
        try:
            imports = parse_imports(path, current_module=module_name)
        except SyntaxError:
            continue
        for imported in imports:
            if imported.startswith("app."):
                matches = {name for name in module_names if name == imported}
                package_init = f"{imported}.__init__"
                if package_init in module_names:
                    matches.add(package_init)
                matches.discard(module_name)
                graph[module_name].update(matches)
    return graph


def find_cycles(graph: dict[str, set[str]], limit: int = 20) -> list[list[str]]:
    cycles: list[list[str]] = []
    stack: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if len(cycles) >= limit:
            return
        if node in visiting:
            index = stack.index(node)
            cycles.append(stack[index:] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for child in graph.get(node, set()):
            visit(child)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def missing_init_files(base: Path = APP_DIR) -> list[Path]:
    missing: list[Path] = []
    for folder in sorted(path for path in base.rglob("*") if path.is_dir() and "__pycache__" not in path.parts):
        has_python = any(child.suffix == ".py" for child in folder.iterdir() if child.is_file())
        if has_python and not (folder / "__init__.py").exists():
            missing.append(folder)
    return missing


def inspect_classes(module: ModuleType, suffix: str | None = None) -> list[type[Any]]:
    classes: list[type[Any]] = []
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and (suffix is None or value.__name__.endswith(suffix)):
            classes.append(value)
    return classes


def iter_package_modules(package_name: str) -> list[str]:
    package = import_module(package_name)
    if not hasattr(package, "__path__"):
        return [package_name]
    return sorted(module.name for module in pkgutil.walk_packages(package.__path__, package.__name__ + "."))


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def score_from_results(results: list[CheckResult]) -> int:
    if not results:
        return 0
    ok_count = sum(1 for result in results if result.ok)
    return round((ok_count / len(results)) * 100)
