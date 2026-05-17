from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ENDPOINTS = [
    "/analytics/dashboard",
    "/analytics/capex",
    "/analytics/heatmap",
    "/analytics/risk",
    "/analytics/procurement",
    "/analytics/logistics",
    "/analytics/scenarios",
    "/analytics/drilldown",
    "/analytics/timeline",
    "/analytics/system-health",
    "/analytics/qa-summary",
]


def _load_json_url(url: str, timeout: int) -> tuple[int, dict]:
    with urlopen(url, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def validate_endpoint(base_url: str, endpoint: str, timeout: int) -> dict:
    started = perf_counter()
    url = f"{base_url.rstrip('/')}{endpoint}"
    try:
        http_status, payload = _load_json_url(url, timeout)
        duration_ms = round((perf_counter() - started) * 1000, 2)
        kpis = payload.get("kpis") or {}
        charts = payload.get("charts") or {}
        table = payload.get("table") or []
        ok = http_status == 200 and payload.get("status") == "SUCCESS"
        return {
            "endpoint": endpoint,
            "ok": ok,
            "http_status": http_status,
            "duration_ms": duration_ms,
            "api_status": payload.get("status"),
            "nb_lignes": kpis.get("nb_lignes"),
            "capex_brut": kpis.get("capex_brut"),
            "charts_count": len(charts),
            "table_rows": len(table),
            "warnings": payload.get("warnings") or [],
        }
    except HTTPError as exc:
        return {
            "endpoint": endpoint,
            "ok": False,
            "http_status": exc.code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
            "error": str(exc),
        }
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "endpoint": endpoint,
            "ok": False,
            "http_status": None,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
            "error": str(exc),
        }


def validate_analytics(base_url: str, timeout: int = 30) -> dict:
    results = [validate_endpoint(base_url, endpoint, timeout) for endpoint in ENDPOINTS]
    return {
        "base_url": base_url,
        "status": "PASS" if all(item["ok"] for item in results) else "WARN",
        "endpoints": results,
        "summary": {
            "tested": len(results),
            "ok": sum(1 for item in results if item["ok"]),
            "failed": sum(1 for item in results if not item["ok"]),
            "max_duration_ms": max((item["duration_ms"] for item in results), default=0),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Valide les endpoints SP2I Analytics Engine.")
    parser.add_argument("--base-url", default="https://sp2i-backend.onrender.com")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    report = validate_analytics(args.base_url, args.timeout)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")

    if report["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
