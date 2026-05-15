from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import decision_parameters as params
from app.database import get_db


router = APIRouter()


def _uuid(value: str, prefix: str = "") -> str:
    """
    Accepte les identifiants techniques exposes par l'API (`sim_xxx`) et les
    UUID bruts stockes en PostgreSQL.
    """
    cleaned = value.replace(prefix, "") if prefix and value.startswith(prefix) else value
    return str(UUID(cleaned))


@router.get("/rules")
def get_decision_rules() -> dict:
    """
    Expose les regles decisionnelles actives.

    Le frontend et Power BI peuvent afficher ces parametres pour rendre chaque
    arbitrage comprehensible sans dupliquer la logique metier.
    """
    return {
        "status": "SUCCESS",
        "weights": {
            "savings": params.WEIGHT_SAVINGS,
            "risk": params.WEIGHT_RISK,
            "lead_time": params.WEIGHT_LEAD_TIME,
            "criticality": params.WEIGHT_CRITICALITY,
        },
        "thresholds": {
            "min_import_score": params.MIN_IMPORT_SCORE,
            "min_mixed_score": params.MIN_MIXED_SCORE,
            "high_confidence_score": params.HIGH_CONFIDENCE_SCORE,
            "medium_confidence_score": params.MEDIUM_CONFIDENCE_SCORE,
        },
        "criticality_weights": params.CRITICALITY_WEIGHTS,
        "rules": params.DECISION_RULES,
    }


@router.get("/explain/{simulation_id}")
def explain_decision(simulation_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Retourne l'explication des decisions d'une simulation historisee.

    La table `fact_simulation` reste la source de verite : l'API lit les scores
    et les raisons deja calcules au moment de la simulation.
    """
    simulation_uuid = _uuid(simulation_id, "sim_")
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
                decision_confidence,
                decision_reason,
                risk_score,
                lead_time_score,
                criticality_score,
                economie,
                capex_local,
                capex_optimise
            FROM fact_simulation
            WHERE simulation_id = CAST(:simulation_id AS uuid)
            ORDER BY simulation_line_id
            """
        ),
        {"simulation_id": simulation_uuid},
    ).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="Simulation introuvable.")

    lignes = [dict(row) for row in rows]
    first = lignes[0]
    return jsonable_encoder(
        {
            "status": "SUCCESS",
            "simulation_id": str(first["simulation_id"]),
            "scenario_id": str(first["scenario_id"]),
            "run_id": str(first["run_id"]),
            "metadata": {
                "nombre_lignes": len(lignes),
                "source": "fact_simulation",
            },
            "warnings": [],
            "errors": [],
            "lignes": lignes,
        }
    )


@router.get("/risk-analysis/{scenario_id}")
def risk_analysis(scenario_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Agrège les risques decisionnels d'un scenario pour Power BI et React.
    """
    scenario_uuid = _uuid(scenario_id, "scenario_")
    rows = db.execute(
        text(
            """
            SELECT *
            FROM v_decision_risk
            WHERE scenario_id = CAST(:scenario_id AS uuid)
            ORDER BY risk_level, decision_type
            """
        ),
        {"scenario_id": scenario_uuid},
    ).mappings().all()

    return jsonable_encoder(
        {
            "status": "SUCCESS",
            "scenario_id": scenario_uuid,
            "metadata": {
                "nombre_groupes": len(rows),
                "source": "v_decision_risk",
            },
            "warnings": [],
            "errors": [],
            "risk_analysis": [dict(row) for row in rows],
        }
    )
