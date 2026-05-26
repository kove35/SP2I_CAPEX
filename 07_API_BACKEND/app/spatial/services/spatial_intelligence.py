from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.bim.maturity import detect_bim_maturity_from_columns, enrich_bim_maturity_with_lines
from app.spatial.dependencies.engine import build_spatial_dependency_graph
from app.spatial.events.engine import build_spatial_event_feed
from app.spatial.hierarchy.engine import SpatialHierarchyEngine
from app.spatial.planning.engine import build_spatial_planning_intelligence
from app.spatial.propagation.engine import build_spatial_risk_propagation
from app.spatial.risks.propagation import build_spatial_risk_heatmap
from app.spatial.storage.engine import build_spatial_storage_intelligence
from app.spatial.timeline.engine import build_spatial_timeline


def get_project_spatial_summary(db: Session, project_id: int) -> dict[str, Any]:
    metre_rows = _load_fact_metre_spatial_rows(db, project_id)
    action_rows = _load_execution_action_spatial_rows(db, project_id)
    engine = SpatialHierarchyEngine()
    timeline = build_spatial_timeline(action_rows)
    dependencies = build_spatial_dependency_graph(action_rows)
    event_feed = build_spatial_event_feed(action_rows, timeline)
    planning = build_spatial_planning_intelligence(timeline, dependencies)
    storage = build_spatial_storage_intelligence(action_rows)
    risk_propagation = build_spatial_risk_propagation(event_feed, dependencies)
    maturity = enrich_bim_maturity_with_lines(
        detect_bim_maturity_from_columns(["BATIMENT", "NIVEAU", "APPART", "PIECE", "LOT", "IFC_GUID", "BIM_OBJECT_ID"]),
        metre_rows,
    )
    if not metre_rows:
        maturity = {
            **maturity,
            "maturity": "NON_BIM",
            "mode": "NON_BIM",
            "is_bim_compatible": False,
            "confidence": 0,
        }

    return {
        "project_id": project_id,
        "maturity": maturity,
        "kpis": _spatial_kpis(metre_rows, action_rows),
        "hierarchy": engine.build_tree(metre_rows),
        "capex_by_batiment": engine.aggregate_by_level(metre_rows, "batiment"),
        "capex_by_niveau": engine.aggregate_by_level(metre_rows, "niveau"),
        "capex_by_piece": engine.aggregate_by_level(metre_rows, "piece"),
        "execution_by_space": _execution_by_space(action_rows),
        "risk_heatmap": build_spatial_risk_heatmap(action_rows),
        "timeline": timeline,
        "dependencies": dependencies,
        "event_feed": event_feed,
        "planning": planning,
        "storage": storage,
        "risk_propagation": risk_propagation,
    }


def _load_fact_metre_spatial_rows(db: Session, project_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                COALESCE(NULLIF(batiment, ''), '') AS batiment,
                COALESCE(NULLIF(niveau, ''), '') AS niveau,
                COALESCE(NULLIF(appart, ''), '') AS appart,
                COALESCE(NULLIF(piece, ''), '') AS piece,
                COALESCE(NULLIF(lot, ''), '') AS lot,
                COALESCE(NULLIF(bim_object_id, ''), '') AS bim_object_id,
                COALESCE(NULLIF(ifc_guid, ''), '') AS ifc_guid,
                COUNT(*) AS lines_count,
                COALESCE(SUM(capex_local), SUM(prix_total_ht), 0) AS capex_local,
                COUNT(*) FILTER (WHERE statut_ligne <> 'OK') AS risk_count
            FROM fact_metre
            WHERE COALESCE(projet_id, :project_id) = :project_id
            GROUP BY batiment, niveau, appart, piece, lot, bim_object_id, ifc_guid
            ORDER BY batiment, niveau, appart, piece, lot
            LIMIT 5000
            """
        ),
        {"project_id": project_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def _load_execution_action_spatial_rows(db: Session, project_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                id,
                COALESCE(NULLIF(batiment, ''), '') AS batiment,
                COALESCE(NULLIF(niveau, ''), '') AS niveau,
                COALESCE(NULLIF(appart, ''), '') AS appart,
                COALESCE(NULLIF(piece, ''), '') AS piece,
                COALESCE(NULLIF(lot, ''), '') AS lot,
                title,
                problem,
                recommended_action,
                status,
                risk_level,
                priority,
                action_type,
                due_date,
                delivery_eta_days,
                delay_days,
                storage_impact,
                criticality_score
            FROM site_execution_actions
            WHERE project_id = :project_id
            ORDER BY batiment, niveau, piece, priority
            LIMIT 5000
            """
        ),
        {"project_id": project_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def _spatial_kpis(metre_rows: list[dict[str, Any]], action_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "spatialized_lines_count": sum(int(row.get("lines_count") or 0) for row in metre_rows if row.get("batiment") or row.get("niveau") or row.get("piece")),
        "batiments_count": len({row.get("batiment") for row in metre_rows if row.get("batiment")}),
        "niveaux_count": len({(row.get("batiment"), row.get("niveau")) for row in metre_rows if row.get("niveau")}),
        "pieces_count": len({(row.get("batiment"), row.get("niveau"), row.get("piece")) for row in metre_rows if row.get("piece")}),
        "bim_objects_count": len({row.get("ifc_guid") or row.get("bim_object_id") for row in metre_rows if row.get("ifc_guid") or row.get("bim_object_id")}),
        "capex_spatialized": round(sum(float(row.get("capex_local") or 0) for row in metre_rows), 2),
        "execution_actions_spatialized": len([row for row in action_rows if row.get("batiment") or row.get("niveau") or row.get("piece")]),
        "spatial_risks_count": len([row for row in action_rows if str(row.get("status") or "").upper() in {"AT_RISK", "BLOCKED"}]),
    }


def _execution_by_space(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for action in actions:
        key = (action.get("batiment") or "", action.get("niveau") or "", action.get("piece") or "")
        bucket = buckets.setdefault(
            key,
            {
                "batiment": key[0],
                "niveau": key[1],
                "piece": key[2],
                "actions_count": 0,
                "open_count": 0,
                "done_count": 0,
                "at_risk_count": 0,
                "blocked_count": 0,
            },
        )
        bucket["actions_count"] += 1
        status = str(action.get("status") or "").upper()
        if status == "DONE":
            bucket["done_count"] += 1
        elif status == "AT_RISK":
            bucket["at_risk_count"] += 1
            bucket["open_count"] += 1
        elif status == "BLOCKED":
            bucket["blocked_count"] += 1
            bucket["open_count"] += 1
        elif status != "CANCELLED":
            bucket["open_count"] += 1
    return list(buckets.values())
