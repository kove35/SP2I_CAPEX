from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter()


def _simulation_uuid(value: str) -> str:
    cleaned = value.replace("sim_", "") if value.startswith("sim_") else value
    return str(UUID(cleaned))


def _load_procurement_rows(simulation_id: str, db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                simulation_id,
                scenario_id,
                run_id,
                id_ligne,
                designation,
                decision_import,
                decision_type,
                decision_score,
                global_risk_score,
                lead_time_days,
                cashflow_score,
                moq_risk_score,
                complexity_score,
                procurement_reason,
                economie,
                capex_import,
                capex_optimise
            FROM fact_simulation
            WHERE simulation_id = CAST(:simulation_id AS uuid)
            ORDER BY simulation_line_id
            """
        ),
        {"simulation_id": _simulation_uuid(simulation_id)},
    ).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="Simulation introuvable.")
    return [dict(row) for row in rows]


def _response(simulation_id: str, section: str, rows: list[dict]) -> dict:
    return jsonable_encoder(
        {
            "status": "SUCCESS",
            "simulation_id": str(rows[0]["simulation_id"]),
            "scenario_id": str(rows[0]["scenario_id"]),
            "metadata": {
                "section": section,
                "nombre_lignes": len(rows),
                "source": "fact_simulation",
            },
            "warnings": [],
            "errors": [],
            section: rows,
        }
    )


@router.get("/risk-analysis/{simulation_id}")
def risk_analysis(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    """Expose les scores de risque procurement historises."""
    rows = _load_procurement_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "global_risk_score": row["global_risk_score"],
            "procurement_reason": row["procurement_reason"],
        }
        for row in rows
    ]
    return _response(simulation_id, "risk_analysis", payload)


@router.get("/lead-time/{simulation_id}")
def lead_time(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    """Expose les delais import calcules pour une simulation."""
    rows = _load_procurement_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "lead_time_days": row["lead_time_days"],
            "procurement_reason": row["procurement_reason"],
        }
        for row in rows
    ]
    return _response(simulation_id, "lead_time_analysis", payload)


@router.get("/cashflow/{simulation_id}")
def cashflow(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    """Expose l'impact cashflow historise."""
    rows = _load_procurement_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "cashflow_score": row["cashflow_score"],
            "capex_import": row["capex_import"],
            "procurement_reason": row["procurement_reason"],
        }
        for row in rows
    ]
    return _response(simulation_id, "cashflow_analysis", payload)


@router.get("/import-complexity/{simulation_id}")
def import_complexity(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    """Expose la complexite import et le risque MOQ."""
    rows = _load_procurement_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "complexity_score": row["complexity_score"],
            "moq_risk_score": row["moq_risk_score"],
            "procurement_reason": row["procurement_reason"],
        }
        for row in rows
    ]
    return _response(simulation_id, "import_complexity_analysis", payload)
