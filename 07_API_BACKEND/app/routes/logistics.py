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


def _load_rows(simulation_id: str, db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                simulation_id,
                scenario_id,
                id_ligne,
                designation,
                container_strategy,
                shipment_strategy,
                fill_rate,
                shipment_cost,
                lead_time_total,
                storage_cost,
                delivery_risk,
                logistics_reason
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


def _response(section: str, rows: list[dict]) -> dict:
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


@router.get("/container-plan/{simulation_id}")
def container_plan(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    rows = _load_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "container_strategy": row["container_strategy"],
            "fill_rate": row["fill_rate"],
            "logistics_reason": row["logistics_reason"],
        }
        for row in rows
    ]
    return _response("container_plan", payload)


@router.get("/shipment-analysis/{simulation_id}")
def shipment_analysis(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    rows = _load_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "shipment_strategy": row["shipment_strategy"],
            "lead_time_total": row["lead_time_total"],
            "delivery_risk": row["delivery_risk"],
            "logistics_reason": row["logistics_reason"],
        }
        for row in rows
    ]
    return _response("shipment_analysis", payload)


@router.get("/freight-cost/{simulation_id}")
def freight_cost(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    rows = _load_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "shipment_cost": row["shipment_cost"],
            "storage_cost": row["storage_cost"],
            "logistics_reason": row["logistics_reason"],
        }
        for row in rows
    ]
    return _response("freight_cost", payload)


@router.get("/site-delivery/{simulation_id}")
def site_delivery(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    rows = _load_rows(simulation_id, db)
    payload = [
        {
            "simulation_id": row["simulation_id"],
            "scenario_id": row["scenario_id"],
            "id_ligne": row["id_ligne"],
            "designation": row["designation"],
            "delivery_risk": row["delivery_risk"],
            "storage_cost": row["storage_cost"],
            "lead_time_total": row["lead_time_total"],
            "logistics_reason": row["logistics_reason"],
        }
        for row in rows
    ]
    return _response("site_delivery", payload)
