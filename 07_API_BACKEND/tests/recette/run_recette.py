"""Recette fonctionnelle : scenarios executés contre le VRAI backend FastAPI
et la base PostgreSQL isolee (aucune interception d'API, aucun mock metier).

Prerequis (voir README.md du dossier recette) :
  - conteneur sp2i_capex_test_pg up ;
  - base sp2i_capex_recipe preparee (prepare_recipe_db.py) ;
  - backend demarre : DATABASE_URL=...sp2i_capex_recipe, port 8000.

Usage :
    python tests/recette/run_recette.py
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent / "run_recette_report.json"

RESULT: list[dict] = []


def _request(method: str, path: str, token: str | None = None, body: dict | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, {"detail": raw}


def check(name: str, ok: bool, detail: str) -> None:
    RESULT.append({"scenario": name, "ok": bool(ok), "detail": detail})
    print(("  OK  " if ok else "  FAIL") + f" {name}: {detail}")
    if not ok:
        raise SystemExit(f"scenario failed: {name}")


def main() -> int:
    print("== 1. Connexion ==")
    status, data = _request("POST", "/auth/login", body={"email": "admin@recette.local", "password": "Admin123!"})
    check("connexion admin", status == 200 and data["user"]["role"] == "ADMIN", f"http={status}")
    admin_token = data["access_token"]

    status, data = _request("POST", "/auth/login", body={"email": "admin@recette.local", "password": "wrong"})
    check("mauvais mot de passe rejete", status == 401, f"http={status}")

    status, data = _request("POST", "/auth/login", body={"email": "alice@recette.local", "password": "Alice123!"})
    check("connexion analyste", status == 200 and data["user"]["role"] == "ANALYST", f"http={status}")
    alice_token = data["access_token"]

    def get(path: str, token: str):
        s, d = _request("GET", path, token=token)
        return s, d

    print("== 2. Changement de projet ==")
    s, a = get("/analytics/v6/project-cost?projet=PROJET_A", admin_token)
    s2, b = get("/analytics/v6/project-cost?projet=PROJET_B", admin_token)
    check("projet A (admin)", s == 200 and a["kpis"]["capex_direct"] == 3000.0, f"capex_direct={a['kpis']['capex_direct']}")
    check("projet B (admin)", s2 == 200 and b["kpis"]["capex_direct"] == 500.0, f"capex_direct={b['kpis']['capex_direct']}")
    check("changement projet isole (A != B)", a["kpis"]["capex_direct"] != b["kpis"]["capex_direct"], "3000 != 500")

    print("== 3. Projet vide ==")
    s, c = get("/analytics/v6/project-cost?projet=PROJET_C", admin_token)
    zeros = all(float(c["kpis"].get(k) or 0) == 0.0 for k in
                ("capex_direct", "capex_import", "total_project_cost", "indirect_costs"))
    check("projet vide repond 200 zeros", s == 200 and zeros, f"http={s} kpis={c['kpis']}")

    print("== 4. Filtre niveau ==")
    s, r = get("/analytics/v6/project-cost?projet=PROJET_A&niveau=RDC", admin_token)
    check("filtre niveau RDC = 1000", s == 200 and r["kpis"]["capex_direct"] == 1000.0,
          f"capex_direct={r['kpis']['capex_direct']}")

    print("== 5. Coherence KPI / graphiques / details ==")
    s, d = get("/analytics/v6/dashboard?projet=PROJET_A", admin_token)
    rows = d["table"]
    sum_lots = round(sum(float(x["capex_direct"]) for x in rows), 2)
    check("dashboard table 3 lots", len(rows) == 3, f"nb_lots={len(rows)}")
    check("somme lots = capex projet", sum_lots == rows[0]["project_capex_direct"] == 3000.0, f"sum={sum_lots}")
    check("KPI total coherent tableau", float(d["kpis"]["total_project_cost"]) == float(rows[0]["total_project_cost"]),
          f"kpi={d['kpis']['total_project_cost']}")
    s, ci = get("/analytics/v6/cost-intelligence?projet=PROJET_A&page_size=100", admin_token)
    ci_rows = ci["table"]
    check("cost-intelligence 4 lignes fines", s == 200 and len(ci_rows) == 4, f"nb_rows={len(ci_rows)}")
    sum_ci = round(sum(float(x["capex_local"]) for x in ci_rows), 2)
    check("somme lignes fines = capex_direct", sum_ci == 3000.0, f"sum={sum_ci}")

    print("== 6. Ratio indisponible ==")
    s, p = get("/analytics/v6/project-cost?projet=PROJET_D&niveau=S1", admin_token)
    k = p["kpis"]
    check("surface non resolvable -> None", k.get("surface_m2") is None, f"surface_m2={k.get('surface_m2')}")
    check("capex_m2 indisponible", k.get("capex_m2") is None, f"capex_m2={k.get('capex_m2')}")
    check("total_project_cost_per_m2 indisponible", k.get("total_project_cost_per_m2") is None,
          f"tpc_m2={k.get('total_project_cost_per_m2')}")

    print("== 7. Refus d'acces projet non autorise ==")
    s, _ = get("/analytics/v6/project-cost?projet=PROJET_A", alice_token)
    check("analyste autorise projet A", s == 200, f"http={s}")
    s, e = get("/analytics/v6/project-cost?projet=PROJET_B", alice_token)
    check("analyste refuse projet B (404)", s == 404, f"http={s} detail={e.get('detail')}")
    s, e = get("/analytics/v6/project-cost", alice_token)
    check("analyste sans projet refuse (403)", s == 403, f"http={s} detail={e.get('detail')}")

    print("\nALL_RECIPE_SCENARIOS_PASSED")
    OUT.write_text(json.dumps(RESULT, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
