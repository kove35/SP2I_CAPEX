from __future__ import annotations

import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.projects.models import Project


EMPTY = "-"
MONEY_COLUMNS = {"Coût local estimé", "Coût import estimé", "Économie estimée", "Budget local", "Budget optimisé", "Économie nette"}
PERCENT_COLUMNS = {"Taux économie"}
PROCUREMENT_REVIEW_STATUSES = {"PENDING", "TO_ARBITRATE", "REVIEW_REQUIRED", "BLOCKED"}
PROCUREMENT_RISK_STATUSES = {"TO_ARBITRATE", "REVIEW_REQUIRED", "BLOCKED"}
RISK_LEVELS = {"HIGH", "CRITICAL"}


def safe_value(value: Any) -> Any:
    if value is None or value == "":
        return EMPTY
    return value


def format_currency(value: Any) -> Any:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return EMPTY
    return numeric if numeric else EMPTY


def format_percent(value: Any) -> Any:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return EMPTY
    if not numeric:
        return EMPTY
    return numeric if numeric > 1 else numeric * 100


def generate_procurement_export_filename(project: Project | Any) -> str:
    raw_name = getattr(project, "name", None) or "Projet"
    name = re.sub(r"[^A-Za-z0-9]+", "_", raw_name).strip("_") or "Projet"
    date = datetime.now(timezone.utc).date().isoformat()
    return f"Dossier_Achat_SP2I_{name}_{date}.xlsx"


def _query_all(db: Session, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in db.execute(text(sql), params).mappings().all()]
    except SQLAlchemyError:
        return []


def _query_one(db: Session, sql: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        row = db.execute(text(sql), params).mappings().first()
        return dict(row) if row else {}
    except SQLAlchemyError:
        return {}


def _scenario_context(db: Session, project_id: int) -> dict[str, Any]:
    return _query_one(
        db,
        """
        SELECT
            ds.scenario_id::text AS scenario_id,
            ds.scenario_nom,
            ds.scenario_type,
            sr.run_id::text AS run_id,
            sr.status AS run_status,
            COALESCE(sr.ended_at, sr.started_at, ds.updated_at, ds.created_at) AS simulated_at,
            COALESCE(sr.rows_out, 0) AS rows_out,
            COUNT(fs.simulation_line_id) AS line_count,
            COALESCE(SUM(fs.capex_local), 0) AS budget_local,
            COALESCE(SUM(fs.capex_optimise), 0) AS budget_optimise,
            COALESCE(SUM(fs.economie), 0) AS economie_nette,
            COUNT(*) FILTER (WHERE UPPER(COALESCE(fs.decision_import, '')) = 'IMPORT') AS import_lines_count,
            COUNT(*) FILTER (WHERE UPPER(COALESCE(fs.decision_import, '')) = 'LOCAL') AS local_lines_count,
            COUNT(*) FILTER (WHERE UPPER(COALESCE(fs.decision_import, '')) IN ('HYBRID', 'HYBRIDE', 'MIXTE')) AS hybrid_lines_count,
            MAX(fs.global_risk_score) AS risk_score
        FROM simulation_run sr
        JOIN dim_scenario ds ON ds.scenario_id = sr.scenario_id
        LEFT JOIN fact_simulation fs ON fs.run_id = sr.run_id
        WHERE sr.projet_id = :project_id
          AND sr.status IN ('SUCCESS', 'READY', 'SIMULATED', 'VALIDATED')
        GROUP BY
            ds.scenario_id,
            ds.scenario_nom,
            ds.scenario_type,
            ds.created_at,
            ds.updated_at,
            sr.run_id,
            sr.status,
            sr.started_at,
            sr.ended_at,
            sr.rows_out
        HAVING COALESCE(sr.rows_out, 0) > 0 OR COUNT(fs.simulation_line_id) > 0
        ORDER BY COALESCE(sr.ended_at, sr.started_at, ds.updated_at, ds.created_at) DESC
        LIMIT 1
        """,
        {"project_id": project_id},
    )


def _procurement_decisions(db: Session, project_id: int, scenario_id: str | None = None) -> list[dict[str, Any]]:
    filters = ["project_id = :project_id"]
    params: dict[str, Any] = {"project_id": project_id}
    if scenario_id:
        filters.append("scenario_id = :scenario_id")
        params["scenario_id"] = scenario_id
    return _query_all(
        db,
        f"""
        SELECT *
        FROM procurement_decisions
        WHERE {" AND ".join(filters)}
        ORDER BY
            CASE validation_status
                WHEN 'BLOCKED' THEN 1
                WHEN 'REVIEW_REQUIRED' THEN 2
                WHEN 'TO_ARBITRATE' THEN 3
                WHEN 'PENDING' THEN 4
                WHEN 'VALIDATED' THEN 5
                WHEN 'REJECTED' THEN 6
                ELSE 7
            END,
            risk_level DESC,
            id
        """,
        params,
    )


def _workflow_events(db: Session, project_id: int) -> list[dict[str, Any]]:
    return _query_all(
        db,
        """
        SELECT *
        FROM workflow_events
        WHERE project_id = :project_id
        ORDER BY created_at DESC, id DESC
        LIMIT 500
        """,
        {"project_id": project_id},
    )


def _execution_actions(db: Session, project_id: int, scenario_id: str | None = None) -> list[dict[str, Any]]:
    filters = ["project_id = :project_id"]
    params: dict[str, Any] = {"project_id": project_id}
    if scenario_id:
        filters.append("scenario_id = :scenario_id")
        params["scenario_id"] = scenario_id
    return _query_all(
        db,
        f"""
        SELECT *
        FROM site_execution_actions
        WHERE {" AND ".join(filters)}
        ORDER BY
            CASE priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
            id
        """,
        params,
    )


def _dqe_context(db: Session, project_id: int) -> dict[str, Any]:
    return _query_one(
        db,
        """
        SELECT
            file_name,
            status,
            trust_score,
            normalized_lines_count,
            synced_at
        FROM dqe_versions
        WHERE project_id = :project_id AND is_active = true
        ORDER BY uploaded_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        {"project_id": project_id},
    )


def _procurement_counts(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "decisions_count": len(decisions),
        "validated_count": 0,
        "pending_count": 0,
        "to_arbitrate_count": 0,
        "blocked_count": 0,
        "review_required_count": 0,
        "critical_risk_count": 0,
        "high_risk_count": 0,
    }
    for decision in decisions:
        status = str(decision.get("validation_status") or "").upper()
        risk = str(decision.get("risk_level") or "").upper()
        if status == "VALIDATED":
            counts["validated_count"] += 1
        if status == "PENDING":
            counts["pending_count"] += 1
        if status == "TO_ARBITRATE":
            counts["to_arbitrate_count"] += 1
        if status == "BLOCKED":
            counts["blocked_count"] += 1
        if status == "REVIEW_REQUIRED":
            counts["review_required_count"] += 1
        if risk == "CRITICAL":
            counts["critical_risk_count"] += 1
        if risk == "HIGH":
            counts["high_risk_count"] += 1
    return counts


def _action_expected(status: str) -> str:
    status = str(status or "").upper()
    if status == "PENDING":
        return "Valider ou ajuster la décision achat"
    if status == "TO_ARBITRATE":
        return "Arbitrage achat requis"
    if status == "REVIEW_REQUIRED":
        return "Validation humaine requise"
    if status == "BLOCKED":
        return "Blocage à lever avant engagement"
    return "-"


def _write_table(sheet, headers: list[str], rows: list[list[Any]], empty_message: str | None = None) -> None:
    header_fill = PatternFill("solid", fgColor="0B1728")
    header_font = Font(color="FFFFFF", bold=True)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(vertical="center")
    if rows:
        for row in rows:
            sheet.append([safe_value(value) for value in row])
    elif empty_message:
        sheet.append([empty_message])
    sheet.freeze_panes = "A2"
    if rows:
        sheet.auto_filter.ref = sheet.dimensions
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            header = headers[cell.column - 1] if cell.column - 1 < len(headers) else ""
            if header in MONEY_COLUMNS and isinstance(cell.value, (int, float)):
                cell.number_format = '#,##0 "FCFA"'
            if header in PERCENT_COLUMNS and isinstance(cell.value, (int, float)):
                cell.number_format = '0.0"%"'
    for column_cells in sheet.columns:
        width = max(len(str(cell.value or "")) for cell in column_cells) + 2
        sheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(max(width, 14), 55)


def build_procurement_export_from_data(
    project: Project | Any,
    workflow: dict[str, Any],
    scenario: dict[str, Any],
    dqe: dict[str, Any],
    decisions: list[dict[str, Any]],
    workflow_events: list[dict[str, Any]],
    execution_actions: list[dict[str, Any]],
) -> BytesIO:
    workbook = Workbook()
    counts = _procurement_counts(decisions)
    export_date = datetime.now(timezone.utc)
    dossier_status = "Prêt" if counts["decisions_count"] and counts["blocked_count"] == 0 and counts["review_required_count"] == 0 else "Provisoire"

    sheet = workbook.active
    sheet.title = "Synthèse projet"
    _write_table(
        sheet,
        ["Indicateur", "Valeur"],
        [
            ["Nom projet", getattr(project, "name", "")],
            ["Client / organisation", getattr(project, "client_name", "")],
            ["Ville", getattr(project, "city", "")],
            ["Pays", getattr(project, "country", "")],
            ["Devise", getattr(project, "currency", "")],
            ["Responsable projet", getattr(project, "project_manager", "")],
            ["Statut workflow global", workflow.get("label") or workflow.get("status")],
            ["Prochaine action recommandée", (workflow.get("primary_action") or {}).get("label")],
            ["Date export", export_date.strftime("%Y-%m-%d %H:%M")],
            ["Statut du dossier achat", dossier_status],
            ["DQE actif", dqe.get("file_name") or dqe.get("status")],
            ["Trust score DQE", dqe.get("trust_score")],
            ["Budget local", format_currency(scenario.get("budget_local"))],
            ["Budget optimisé", format_currency(scenario.get("budget_optimise"))],
            ["Économie estimée", format_currency(scenario.get("economie_nette"))],
            ["Taux économie", format_percent((float(scenario.get("economie_nette") or 0) / float(scenario.get("budget_local") or 0)) if scenario.get("budget_local") else None)],
            ["Scénario actif", scenario.get("scenario_nom")],
            ["Nombre de décisions achat", counts["decisions_count"] or EMPTY],
            ["Nombre de décisions validées", counts["validated_count"] or EMPTY],
            ["Nombre de décisions en attente", counts["pending_count"] or EMPTY],
            ["Nombre de décisions à arbitrer", counts["to_arbitrate_count"] or EMPTY],
            ["Nombre de décisions bloquées", counts["blocked_count"] or EMPTY],
        ],
    )

    scenario_sheet = workbook.create_sheet("Scénario actif")
    if scenario:
        taux = (float(scenario.get("economie_nette") or 0) / float(scenario.get("budget_local") or 0)) if scenario.get("budget_local") else None
        scenario_rows = [
            ["Scenario ID", scenario.get("scenario_id")],
            ["Nom scénario", scenario.get("scenario_nom")],
            ["Statut scénario", scenario.get("run_status")],
            ["Date simulation", scenario.get("simulated_at")],
            ["Budget local", format_currency(scenario.get("budget_local"))],
            ["Budget optimisé", format_currency(scenario.get("budget_optimise"))],
            ["Économie nette", format_currency(scenario.get("economie_nette"))],
            ["Taux économie", format_percent(taux)],
            ["Lignes import", scenario.get("import_lines_count")],
            ["Lignes local", scenario.get("local_lines_count")],
            ["Lignes hybrides", scenario.get("hybrid_lines_count")],
            ["Niveau de risque", scenario.get("risk_score")],
            ["Source scénario", "simulation_run / fact_simulation"],
        ]
        _write_table(scenario_sheet, ["Champ", "Valeur"], scenario_rows)
    else:
        _write_table(scenario_sheet, ["Message"], [], "Aucun scénario actif disponible pour ce projet.")

    decision_headers = [
        "ID décision", "Lot", "Famille", "Désignation", "Quantité", "Unité", "Décision IA", "Score IA",
        "Justification IA", "Décision proposée", "Décision validée", "Statut validation", "Fournisseur retenu",
        "Pays fournisseur", "Mode achat", "Coût local estimé", "Coût import estimé", "Économie estimée",
        "Niveau de risque", "Validateur", "Date validation", "Commentaire",
    ]
    decision_rows = [[
        row.get("id"), row.get("lot"), row.get("family"), row.get("designation"), row.get("quantity"), row.get("unit"),
        row.get("ai_decision"), row.get("ai_score"), row.get("ai_reason"), row.get("proposed_decision"),
        row.get("validated_decision"), row.get("validation_status"), row.get("supplier_selected"), row.get("supplier_country"),
        row.get("purchase_mode"), format_currency(row.get("estimated_local_cost")), format_currency(row.get("estimated_import_cost")),
        format_currency(row.get("estimated_savings")), row.get("risk_level"), row.get("validator_name"), row.get("validated_at"),
        row.get("comment"),
    ] for row in decisions]
    _write_table(workbook.create_sheet("Décisions achat"), decision_headers, decision_rows, "Aucune décision achat disponible.")

    review_rows = [[
        row.get("lot"), row.get("family"), row.get("designation"), row.get("ai_decision"), row.get("proposed_decision"),
        row.get("validation_status"), row.get("risk_level"), format_currency(row.get("estimated_savings")),
        row.get("ai_reason"), _action_expected(row.get("validation_status")), row.get("validator_name") or "Responsable achat", row.get("comment"),
    ] for row in decisions if str(row.get("validation_status") or "").upper() in PROCUREMENT_REVIEW_STATUSES]
    _write_table(
        workbook.create_sheet("Arbitrages à valider"),
        ["Lot", "Famille", "Désignation", "Décision IA", "Décision proposée", "Statut validation", "Niveau de risque", "Économie estimée", "Motif IA", "Action attendue", "Responsable", "Commentaire"],
        review_rows,
        "Aucun arbitrage achat à valider.",
    )

    risk_sheet = workbook.create_sheet("Risques achat")
    risk_rows = [
        ["Nombre risques critiques", counts["critical_risk_count"] or EMPTY, "", "", "", "", "", "", ""],
        ["Nombre risques élevés", counts["high_risk_count"] or EMPTY, "", "", "", "", "", "", ""],
        ["Nombre arbitrages requis", counts["to_arbitrate_count"] or EMPTY, "", "", "", "", "", "", ""],
        ["Nombre blocages", counts["blocked_count"] or EMPTY, "", "", "", "", "", "", ""],
    ]
    risk_rows.extend([[
        row.get("lot"), row.get("family"), row.get("designation"), row.get("risk_level"), row.get("validation_status"),
        row.get("proposed_decision"), "Engagement achat ou planning à sécuriser", _action_expected(row.get("validation_status")), row.get("comment"),
    ] for row in decisions if str(row.get("risk_level") or "").upper() in RISK_LEVELS or str(row.get("validation_status") or "").upper() in PROCUREMENT_RISK_STATUSES])
    _write_table(risk_sheet, ["Lot", "Famille", "Désignation", "Risque", "Statut validation", "Décision proposée", "Impact potentiel", "Action recommandée", "Commentaire"], risk_rows, "Aucun risque achat identifié.")

    event_rows = [[
        row.get("created_at"), row.get("event_type"), row.get("entity_type"), row.get("entity_id"),
        row.get("previous_status"), row.get("new_status"), row.get("message"), row.get("user_id"), row.get("metadata_json"),
    ] for row in workflow_events]
    _write_table(
        workbook.create_sheet("Historique workflow"),
        ["Date", "Type événement", "Entité", "ID entité", "Ancien statut", "Nouveau statut", "Message", "Utilisateur", "Métadonnées"],
        event_rows,
        "Aucun événement workflow disponible pour le moment.",
    )

    action_rows = [[
        row.get("priority"), row.get("lot"), row.get("family"), row.get("designation"), row.get("action_type"),
        row.get("problem"), row.get("impact"), row.get("recommended_action"), row.get("responsible_name") or row.get("responsible_role"),
        row.get("due_date"), row.get("status"), row.get("risk_level"), row.get("source"),
    ] for row in execution_actions]
    _write_table(
        workbook.create_sheet("Actions chantier"),
        ["Priorité", "Lot", "Famille", "Désignation", "Type action", "Problème", "Impact chantier", "Action recommandée", "Responsable", "Échéance", "Statut", "Risque", "Source"],
        action_rows,
        "Aucune action chantier générée pour ce projet.",
    )

    _write_table(
        workbook.create_sheet("Paramètres export"),
        ["Paramètre", "Valeur"],
        [
            ["Date génération", export_date.strftime("%Y-%m-%d %H:%M")],
            ["Version SP2I", "SP2I_CAPEX"],
            ["Source données", "projects / workflow / procurement_decisions / workflow_events / site_execution_actions"],
            ["Project ID", getattr(project, "id", "")],
            ["Scenario ID", scenario.get("scenario_id")],
            ["Export généré par", "SP2I"],
            ["Statut dossier", dossier_status],
            ["Notes", "Export Excel projet. Les données inconnues sont indiquées par —."],
        ],
    )

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def build_procurement_export_workbook(project_id: int, db: Session, workflow: dict[str, Any] | None = None) -> BytesIO:
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found")
    scenario = _scenario_context(db, project_id)
    scenario_id = scenario.get("scenario_id")
    decisions = _procurement_decisions(db, project_id, scenario_id=scenario_id)
    events = _workflow_events(db, project_id)
    actions = _execution_actions(db, project_id, scenario_id=scenario_id)
    dqe = _dqe_context(db, project_id)
    return build_procurement_export_from_data(project, workflow or {}, scenario, dqe, decisions, events, actions)
