from __future__ import annotations

from _common import CheckResult, import_module, print_result, print_summary, timed_check, title
from validate_routes import load_app


def check_powerbi_routes() -> tuple[bool, str, list[str]]:
    app = load_app()
    expected = ["/capex/summary", "/fact_metre", "/analytics/dashboard", "/analytics/kpis"]
    paths = {getattr(route, "path", "") for route in app.routes}
    missing = [path for path in expected if path not in paths]
    details = [f"{path}=present" for path in expected if path in paths] + [f"{path}=missing" for path in missing]
    return not missing, "routes Power BI readiness inspectees", details


def check_powerbi_config_flags() -> tuple[bool, str, list[str]]:
    try:
        config = import_module("app.main").debug_config()
        dashboards = config.get("powerbi_dashboards_configured", {})
        details = [f"{key}={'configured' if value else 'not configured'}" for key, value in dashboards.items()]
        return True, "configuration Power BI lue sans exposer les secrets", details
    except Exception as exc:
        return False, "impossible de lire la configuration Power BI via app.main.debug_config", [str(exc)]


def check_analytics_schema_modules() -> tuple[bool, str, list[str]]:
    modules = [
        "app.analytics.routes.analytics",
        "app.analytics.services.analytics_service",
        "app.analytics.repositories.analytics_repository",
        "app.analytics.sql.views",
    ]
    details = []
    for name in modules:
        import_module(name)
        details.append(f"{name}=importable")
    return True, "modules analytics importables", details


def main() -> int:
    title("DEVTOOLS | Validation Power BI payloads")
    results: list[CheckResult] = [
        timed_check("Routes Power BI", check_powerbi_routes),
        timed_check("Configuration Power BI", check_powerbi_config_flags),
        timed_check("Modules analytics", check_analytics_schema_modules),
    ]
    for result in results:
        print_result(result)
    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())
