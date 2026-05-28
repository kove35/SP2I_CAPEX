from __future__ import annotations

import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.projects.models import Project
from app.services.procurement_decisions import list_procurement_decisions, procurement_decision_status
from app.services.site_execution_actions import execution_action_status, list_site_execution_actions
from app.services.workflow_events import list_workflow_events


EMPTY_VALUE = "—"


def safe_value(value: Any) -> str:
    if value is None:
        return EMPTY_VALUE
    if isinstance(value, str) and not value.strip():
        return EMPTY_VALUE
    if isinstance(value, bool):
        return "Oui" if value else "Non"
    return str(value)


def format_currency(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return EMPTY_VALUE
    if numeric == 0:
        return EMPTY_VALUE
    formatted = f"{numeric:,.0f}".replace(",", " ")
    return f"{formatted} FCFA"


def format_percent(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return EMPTY_VALUE
    if numeric == 0:
        return EMPTY_VALUE
    if abs(numeric) <= 1:
        numeric *= 100
    return f"{numeric:.1f} %"


def format_date(value: Any) -> str:
    if not value:
        return EMPTY_VALUE
    if isinstance(value, str):
        return value
    try:
        return value.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def generate_project_report_filename(project: Project | Any) -> str:
    raw_name = getattr(project, "name", None) or "Projet"
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", raw_name).strip("_") or "Projet"
    date = datetime.now(timezone.utc).date().isoformat()
    return f"Rapport_Projet_SP2I_{cleaned}_{date}.pdf"


def _get_page_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "normal": ParagraphStyle(
            "normal",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
    }


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1728")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _build_key_value_table(rows: list[list[Any]], styles: dict[str, ParagraphStyle]) -> Table:
    safe_rows = [[safe_value(cell) for cell in row] for row in rows]
    table = Table(safe_rows, colWidths=[6 * cm, 10 * cm], hAlign="LEFT")
    table.setStyle(_table_style())
    return table


def _build_table(headers: list[str], rows: list[list[Any]]) -> Table:
    data = [headers] + [[safe_value(value) for value in row] for row in rows]
    table = Table(data, repeatRows=1, colWidths=[None] * len(headers), hAlign="LEFT")
    table.setStyle(_table_style())
    return table


def _scenario_context(db: Session, project_id: int) -> dict[str, Any]:
    try:
        row = db.execute(
            text(
                """
                SELECT
                    ds.scenario_id::text AS scenario_id,
                    ds.scenario_nom AS scenario_name,
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
                """
            ),
            {"project_id": project_id},
        ).mappings().first()
    except Exception:
        return {}

    return dict(row) if row else {}


def _resolve_project_dqe_status(db: Session, project_id: int) -> dict[str, Any]:
    latest_audit = None
    total_rows = 0
    try:
        latest_audit = _fetch_latest_dqe_audit(db)
        total_rows = int(db.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar_one() or 0)
    except Exception:
        latest_audit = None
        total_rows = 0

    file_name = ""
    trust_score = 0
    normalized_lines_count = 0
    ignored_lines_count = 0
    data_loss_count = 0
    review_required_count = 0
    certification_status = "UNKNOWN"
    governance_status = None
    synced_at = None

    if latest_audit:
        file_name = latest_audit.get("fichier") or ""
        trust_score = int(latest_audit.get("score_qualite") or 0)
        normalized_lines_count = int(latest_audit.get("lignes_parsees") or 0)
        ignored_lines_count = int(latest_audit.get("lignes_ignorees") or 0)
        review_required_count = int(latest_audit.get("lignes_review_required") or 0)
        data_loss_count = int(latest_audit.get("lignes_rejetees") or 0)
        governance_quality = latest_audit.get("governance_quality") or {}
        governance_status = "DATA_QUALITY_GOVERNANCE" if governance_quality else "UNKNOWN"
        if review_required_count > 0:
            certification_status = "REVIEW_REQUIRED"
        elif int(latest_audit.get("lignes_warning") or 0) > 0:
            certification_status = "CERTIFIED_WITH_WARNINGS"
        else:
            certification_status = "CERTIFIED"
        synced_at = latest_audit.get("created_at") if total_rows > 0 else None

    if latest_audit and total_rows > 0:
        status = "SYNCED"
    elif latest_audit:
        status = certification_status
    else:
        status = "NOT_IMPORTED"

    return {
        "status": status,
        "version_number": 1 if latest_audit else 0,
        "file_name": file_name,
        "certification_status": certification_status,
        "governance_status": governance_status,
        "trust_score": trust_score,
        "normalized_lines_count": normalized_lines_count,
        "ignored_lines_count": ignored_lines_count,
        "data_loss_count": data_loss_count,
        "review_required_count": review_required_count,
        "is_active": status not in {"NOT_IMPORTED"},
        "uploaded_at": None,
        "analyzed_at": None,
        "synced_at": synced_at,
    }


def _fetch_latest_dqe_audit(db: Session) -> Any | None:
    base_select = """
        SELECT fichier, score_qualite, lignes_parsees, lignes_fact_metre, lignes_review_required,
               lignes_warning, lignes_ignorees, {loss_column} AS lignes_rejetees, governance_quality, created_at
        FROM dqe_import_audit
        ORDER BY created_at DESC
        LIMIT 1
    """
    try:
        return db.execute(text(base_select.format(loss_column="lignes_rejetees"))).mappings().first()
    except Exception:
        return db.execute(text(base_select.format(loss_column="0"))).mappings().first()


def _resolve_project_budget_status(db: Session, dqe_status: dict[str, Any]) -> dict[str, Any]:
    lines_count = 0
    total_amount = 0.0
    is_synced = False
    synced_at = None
    message = "Budget non synchronisé."
    status = "SYNC_REQUIRED"

    try:
        lines_count = int(db.execute(text("SELECT COUNT(*) FROM fact_metre")).scalar_one() or 0)
        total_amount = float(db.execute(text("SELECT COALESCE(SUM(capex_local), 0) FROM fact_metre")).scalar_one() or 0.0)
        is_synced = lines_count > 0 and total_amount > 0.0
        synced_at = dqe_status.get("synced_at") if is_synced else None
        if is_synced:
            status = "SYNCED"
            message = "Budget synchronisé dans PostgreSQL."
        elif lines_count > 0:
            message = "Des lignes FACT_METRE existent, mais le budget n'est pas encore marqué comme synchronisé."
        else:
            message = "Aucune ligne FACT_METRE synchronisée."
    except Exception:
        status = "SYNC_REQUIRED"
        message = "Impossible de déterminer le statut de synchronisation du budget."

    return {
        "status": status,
        "is_synced": is_synced,
        "synced_at": synced_at,
        "lines_count": lines_count,
        "total_amount": round(total_amount, 2),
        "source": "FACT_METRE",
        "message": message,
    }


def _build_scenario_status(scenario_context: dict[str, Any]) -> dict[str, Any]:
    if not scenario_context:
        return {
            "status": "NOT_STARTED",
            "is_ready": False,
            "scenario_id": None,
            "scenario_name": EMPTY_VALUE,
            "scenario_type": EMPTY_VALUE,
            "simulated_at": None,
            "rows_out": 0,
            "line_count": 0,
            "budget_local": 0,
            "budget_optimise": 0,
            "economie_nette": 0,
        }

    run_status = scenario_context.get("run_status") or "READY"
    is_ready = run_status in {"SUCCESS", "READY", "SIMULATED", "VALIDATED"} and bool(scenario_context.get("rows_out"))
    return {
        "scenario_id": scenario_context.get("scenario_id"),
        "scenario_name": scenario_context.get("scenario_name"),
        "scenario_type": scenario_context.get("scenario_type"),
        "status": run_status,
        "simulated_at": scenario_context.get("simulated_at"),
        "rows_out": scenario_context.get("rows_out"),
        "line_count": scenario_context.get("line_count"),
        "budget_local": scenario_context.get("budget_local"),
        "budget_optimise": scenario_context.get("budget_optimise"),
        "economie_nette": scenario_context.get("economie_nette"),
        "risk_score": scenario_context.get("risk_score"),
        "is_ready": is_ready,
    }


def _build_workflow_summary(project: Project, dqe_status: dict[str, Any], budget_status: dict[str, Any], scenario_status: dict[str, Any], procurement_status: dict[str, Any], execution_status: dict[str, Any]) -> dict[str, Any]:
    configured = project.setup_status == "CONFIGURED"
    budget_synced = bool(budget_status.get("is_synced"))
    scenario_ready = bool(scenario_status.get("is_ready"))
    procurement_ready = bool(procurement_status.get("is_ready"))
    execution_ready = bool(execution_status.get("is_ready"))

    steps = [
        {"id": "configuration", "label": "Configuration", "status": "Terminé" if configured else "À compléter", "state": "done" if configured else "blocking", "action": "Modifier" if configured else "Configurer", "route": "/app/projects"},
        {"id": "dqe", "label": "DQE", "status": dqe_status.get("status", EMPTY_VALUE), "state": "done" if dqe_status.get("status") in {"CERTIFIED", "CERTIFIED_WITH_WARNINGS", "SYNCED"} else "progress" if dqe_status.get("status") not in {"NOT_IMPORTED"} else "todo", "action": "Vérifier", "route": "/app/dqe?tab=quality"},
        {"id": "budget", "label": "Budget", "status": "Synchronisé" if budget_synced else "À synchroniser", "state": "done" if budget_synced else "todo", "action": "Synchroniser", "route": "/app/dqe?tab=sync"},
        {"id": "scenarios", "label": "Scénarios", "status": "Simulé" if scenario_ready else "Prêt" if budget_synced else "Bloqué", "state": "done" if scenario_ready else "todo" if budget_synced else "blocked", "action": "Tester", "route": "/app/simulation"},
        {"id": "procurement", "label": "Approvisionnement", "status": procurement_status.get("status", EMPTY_VALUE), "state": "done" if procurement_ready else "progress" if procurement_status.get("status") == "REVIEW_REQUIRED" else "todo" if scenario_ready else "blocked", "action": "Préparer", "route": "/app/procurement"},
        {"id": "execution", "label": "Préparation Chantier", "status": execution_status.get("status", EMPTY_VALUE), "state": "done" if execution_ready else "todo" if procurement_ready else "blocked", "action": "Suivre", "route": "/app/site?tab=planning"},
    ]

    if not configured:
        status = "CONFIG_REQUIRED"
        label = "Configuration requise"
        primary_action = {"label": "Configurer le projet", "route": "/app/projects"}
    elif dqe_status.get("status") == "NOT_IMPORTED":
        status = "DQE_REQUIRED"
        label = "DQE à importer"
        primary_action = {"label": "Importer le DQE", "route": "/app/dqe?tab=import"}
    elif dqe_status.get("status") in {"CERTIFIED", "CERTIFIED_WITH_WARNINGS", "SYNCED"} and not budget_synced:
        status = "BUDGET_SYNC_REQUIRED"
        label = "Budget à synchroniser"
        primary_action = {"label": "Synchroniser le budget", "route": "/app/dqe?tab=sync"}
    elif budget_synced and not scenario_ready:
        status = "BUDGET_SYNCED"
        label = "Budget synchronisé"
        primary_action = {"label": "Tester un scénario", "route": "/app/simulation"}
    elif procurement_status.get("status") == "REQUIRED":
        status = "SCENARIO_READY"
        label = "Scénario disponible"
        primary_action = {"label": "Préparer l'approvisionnement", "route": "/app/procurement"}
    elif procurement_status.get("status") == "REVIEW_REQUIRED":
        status = "PROCUREMENT_REVIEW_REQUIRED"
        label = "Arbitrages achat à valider"
        primary_action = {"label": "Valider les arbitrages achat", "route": "/app/procurement"}
    elif procurement_ready:
        if execution_ready:
            status = "EXECUTION_READY"
            label = "Préparation chantier prête"
            primary_action = {"label": "Ouvrir Préparation Chantier", "route": "/app/site?tab=planning"}
        else:
            status = "PROCUREMENT_READY"
            label = "Approvisionnement prêt"
            primary_action = {"label": "Préparer le chantier", "route": "/app/site?tab=planning"}
    else:
        status = "ACTIVE"
        label = "Projet actif"
        primary_action = {"label": "Ouvrir le workspace", "route": "/app"}

    return {
        "status": status,
        "label": label,
        "completion": round((sum(1 for step in steps if step["state"] == "done") / len(steps)) * 100),
        "steps": steps,
        "primary_action": primary_action,
        "dqe": dqe_status,
        "budget": budget_status,
        "scenario": scenario_status,
        "procurement": procurement_status,
        "execution": execution_status,
    }


def _render_cover_page(elements: list[Any], project: Project, workflow: dict[str, Any], styles: dict[str, ParagraphStyle]) -> None:
    elements.append(Spacer(1, 2 * cm))
    elements.append(Paragraph("Rapport projet SP2I", styles["title"]))
    elements.append(Paragraph(safe_value(project.name), styles["subtitle"]))
    elements.append(Spacer(1, 0.2 * cm))

    table = _build_key_value_table(
        [
            ["Client / organisation", project.client_name or EMPTY_VALUE],
            ["Ville", project.city or EMPTY_VALUE],
            ["Pays", project.country or EMPTY_VALUE],
            ["Responsable projet", project.project_manager or EMPTY_VALUE],
            ["Statut global", workflow.get("label", EMPTY_VALUE)],
            ["Prochaine action", workflow.get("primary_action", {}).get("label", EMPTY_VALUE)],
            ["Date export", format_date(datetime.now(timezone.utc))],
        ],
        styles,
    )
    elements.append(table)
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("SP2I — Rapport projet professionnel", styles["small"]))


def _render_section(elements: list[Any], title: str, text: str | None, styles: dict[str, ParagraphStyle]) -> None:
    elements.append(Paragraph(title, styles["section"]))
    if text:
        elements.append(Paragraph(text, styles["normal"]))
    elements.append(Spacer(1, 0.2 * cm))


def _build_report_rows(workflow: dict[str, Any]) -> list[list[str]]:
    if not workflow:
        return []
    return [
        ["Configuration", workflow.get("steps", [])[0].get("status", EMPTY_VALUE) if workflow.get("steps") else EMPTY_VALUE],
        ["DQE", workflow.get("steps", [])[1].get("status", EMPTY_VALUE) if workflow.get("steps") else EMPTY_VALUE],
        ["Budget", workflow.get("steps", [])[2].get("status", EMPTY_VALUE) if workflow.get("steps") else EMPTY_VALUE],
        ["Scénarios", workflow.get("steps", [])[3].get("status", EMPTY_VALUE) if workflow.get("steps") else EMPTY_VALUE],
        ["Approvisionnement", workflow.get("steps", [])[4].get("status", EMPTY_VALUE) if workflow.get("steps") else EMPTY_VALUE],
        ["Préparation Chantier", workflow.get("steps", [])[5].get("status", EMPTY_VALUE) if workflow.get("steps") else EMPTY_VALUE],
    ]


def _build_alerts(workflow: dict[str, Any]) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    steps = {step["id"]: step for step in workflow.get("steps", [])}
    if steps.get("configuration", {}).get("state") != "done":
        alerts.append({"level": "warning", "message": "Configuration projet incomplete.", "recommendation": "Complétez les informations du projet."})
    if steps.get("dqe", {}).get("state") != "done":
        alerts.append({"level": "critical", "message": "DQE absent ou non certifié.", "recommendation": "Importer et certifier le DQE."})
    if steps.get("dqe", {}).get("state") == "done" and steps.get("budget", {}).get("state") != "done":
        alerts.append({"level": "warning", "message": "Budget non synchronisé.", "recommendation": "Synchroniser le budget dans PostgreSQL."})
    if steps.get("budget", {}).get("state") == "done" and steps.get("scenarios", {}).get("state") != "done":
        alerts.append({"level": "warning", "message": "Aucun scénario actif disponible.", "recommendation": "Lancer un scénario CAPEX."})
    procurement = workflow.get("procurement", {})
    if procurement.get("status") == "REVIEW_REQUIRED":
        alerts.append({"level": "warning", "message": "Arbitrages achat à valider.", "recommendation": "Valider les décisions achat."})
    execution = workflow.get("execution", {})
    if execution.get("status") == "AT_RISK":
        alerts.append({"level": "critical", "message": "Préparation chantier à risque.", "recommendation": "Surveiller les lots critiques et ETA."})
    if not alerts:
        alerts.append({"level": "info", "message": "Projet prêt pour pilotage direction.", "recommendation": "Continuer le suivi et la validation."})
    return alerts


def _build_section_table_data(header: list[str], items: list[dict[str, Any]]) -> list[list[str]]:
    rows = []
    for item in items:
        rows.append([safe_value(item.get(col)) for col in header])
    return rows


def _draw_page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(cm, cm * 0.75, "SP2I CAPEX")
    canvas.drawRightString(A4[0] - cm, cm * 0.75, f"Page {doc.page}")
    canvas.restoreState()


def build_project_report_pdf(project_id: int, db: Session) -> BytesIO:
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Projet introuvable: {project_id}")

    dqe_status = _resolve_project_dqe_status(db, project_id)
    budget_status = _resolve_project_budget_status(db, dqe_status)
    scenario_context = _scenario_context(db, project_id)
    scenario_status = _build_scenario_status(scenario_context)

    procurement = procurement_decision_status(db, project_id, scenario_id=scenario_status.get("scenario_id")) or {}
    procurement_rows = list_procurement_decisions(
        db,
        project_id,
        scenario_id=scenario_status.get("scenario_id"),
        limit=20,
    )
    execution = execution_action_status(
        db,
        project_id,
        scenario_id=scenario_status.get("scenario_id"),
        procurement_ready=procurement.get("is_ready", False),
    ) or {}
    execution_rows = list_site_execution_actions(db, project_id, scenario_id=scenario_status.get("scenario_id"), limit=20)
    events = list_workflow_events(db, project_id, limit=20)

    workflow = _build_workflow_summary(
        project,
        dqe_status,
        budget_status,
        scenario_status,
        procurement,
        execution,
    )

    styles = _get_page_styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    elements: list[Any] = []
    _render_cover_page(elements, project, workflow, styles)
    elements.append(PageBreak())

    # Synthese executi
    elements.append(Paragraph("Synthèse exécutive", styles["section"]))
    summary_table = _build_key_value_table(
        [
            ["Statut global du projet", workflow.get("label", EMPTY_VALUE)],
            ["Confiance DQE", safe_value(workflow.get("dqe", {}).get("trust_score"))],
            ["Budget synchronisé", safe_value(workflow.get("budget", {}).get("status"))],
            ["Scénario actif", safe_value(workflow.get("scenario", {}).get("scenario_name") or workflow.get("scenario", {}).get("status"))],
            ["Prochaine action", workflow.get("primary_action", {}).get("label", EMPTY_VALUE)],
            ["Risques majeurs", safe_value(
                ", ".join([alert["message"] for alert in _build_alerts(workflow) if alert["level"] in {"warning", "critical"}])
            )],
        ],
        styles,
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * cm))

    # Workflow
    elements.append(Paragraph("État du workflow projet", styles["section"]))
    workflow_rows = _build_report_rows(workflow)
    if workflow_rows:
        elements.append(_build_table(["Étape", "Statut"], workflow_rows))
    else:
        elements.append(Paragraph("Aucun état workflow disponible.", styles["normal"]))
    elements.append(PageBreak())

    # DQE
    dqe = workflow.get("dqe", {})
    elements.append(Paragraph("Qualité DQE et gouvernance", styles["section"]))
    dqe_rows = [
        ["Fichier actif", dqe.get("file_name") or EMPTY_VALUE],
        ["Certification", dqe.get("certification_status") or dqe.get("status") or EMPTY_VALUE],
        ["Gouvernance", dqe.get("governance_status") or EMPTY_VALUE],
        ["Trust score", safe_value(dqe.get("trust_score"))],
        ["Lignes exploitables", safe_value(dqe.get("normalized_lines_count"))],
        ["Lignes ignorées non critiques", safe_value(dqe.get("ignored_lines_count"))],
        ["Data loss", safe_value(dqe.get("data_loss_count"))],
        ["Review required", safe_value(dqe.get("review_required_count"))],
        ["Synchronisé le", format_date(dqe.get("synced_at"))],
    ]
    elements.append(_build_key_value_table(dqe_rows, styles))
    elements.append(Spacer(1, 0.5 * cm))

    # Budget et scenario
    elements.append(Paragraph("Budget et scénario CAPEX", styles["section"]))
    budget_local = scenario_context.get("budget_local") or workflow.get("budget", {}).get("total_amount")
    budget_optimise = scenario_context.get("budget_optimise") or workflow.get("budget", {}).get("total_amount")
    economie_nette = scenario_context.get("economie_nette") or 0
    taux_economie = (float(economie_nette) / float(budget_local)) if budget_local else 0
    elements.append(_build_key_value_table(
        [
            ["Budget local", format_currency(budget_local)],
            ["Budget optimisé", format_currency(budget_optimise)],
            ["Économie nette", format_currency(economie_nette)],
            ["Taux économie", format_percent(taux_economie)],
            ["Lignes budgétaires synchronisées", safe_value(workflow.get("budget", {}).get("lines_count"))],
            ["Source budget", workflow.get("budget", {}).get("source", EMPTY_VALUE)],
            ["Date synchronisation", format_date(workflow.get("budget", {}).get("synced_at"))],
        ],
        styles,
    ))
    if workflow.get("scenario", {}).get("status") not in {"NOT_STARTED", "UNKNOWN"}:
        elements.append(Spacer(1, 0.3 * cm))
        scenario_rows = [
            ["Scénario actif", workflow.get("scenario", {}).get("scenario_name") or workflow.get("scenario", {}).get("status")],
            ["Type", workflow.get("scenario", {}).get("scenario_type")],
            ["Statut", workflow.get("scenario", {}).get("status")],
            ["Simulé le", format_date(workflow.get("scenario", {}).get("simulated_at"))],
            ["Lignes scénario", safe_value(workflow.get("scenario", {}).get("line_count"))],
            ["Import", safe_value(scenario_context.get("import_lines_count"))],
            ["Local", safe_value(scenario_context.get("local_lines_count"))],
            ["Hybride", safe_value(scenario_context.get("hybrid_lines_count"))],
            ["Risque scénario", safe_value(scenario_context.get("risk_score"))],
        ]
        elements.append(_build_key_value_table(scenario_rows, styles))
    else:
        elements.append(Paragraph("Aucun scénario actif disponible pour ce projet.", styles["normal"]))
    elements.append(PageBreak())

    # Procurement
    elements.append(Paragraph("Approvisionnement et décisions achat", styles["section"]))
    if procurement:
        elements.append(_build_key_value_table(
            [
                ["Total décisions achat", safe_value(procurement.get("decisions_count"))],
                ["Décisions validées", safe_value(procurement.get("validated_decisions_count"))],
                ["Décisions en attente", safe_value(procurement.get("pending_decisions_count"))],
                ["Décisions à arbitrer", safe_value(procurement.get("to_arbitrate_count"))],
                ["Décisions bloquées", safe_value(procurement.get("blocked_decisions_count"))],
                ["Lignes import", safe_value(procurement.get("import_lines_count"))],
                ["Lignes local", safe_value(procurement.get("local_lines_count"))],
                ["Lignes hybride", safe_value(procurement.get("hybrid_lines_count"))],
                ["Fournisseur principal", workflow.get("project_manager") or EMPTY_VALUE],
                ["Statut dossier achat", procurement.get("status", EMPTY_VALUE)],
            ],
            styles,
        ))
    else:
        elements.append(Paragraph("Aucune décision achat disponible.", styles["normal"]))
    if procurement_rows:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("Décisions à risque ou à valider", styles["small"]))
        table_rows = [
            [
                row.get("lot"),
                row.get("family"),
                row.get("designation"),
                row.get("ai_decision"),
                row.get("validated_decision"),
                row.get("validation_status"),
                row.get("risk_level"),
                row.get("comment"),
            ]
            for row in procurement_rows[:20]
        ]
        elements.append(_build_table(["Lot", "Famille", "Désignation", "Décision IA", "Décision validée", "Statut", "Risque", "Commentaire"], table_rows))
    else:
        elements.append(Paragraph("Aucune décision achat disponible.", styles["normal"]))
    elements.append(PageBreak())

    # Preparation chantier
    elements.append(Paragraph("Préparation Chantier", styles["section"]))
    if execution:
        elements.append(_build_key_value_table(
            [
                ["Actions totales", safe_value(execution.get("actions_count"))],
                ["Actions ouvertes", safe_value(execution.get("open_count"))],
                ["Actions terminées", safe_value(execution.get("done_count"))],
                ["Actions à risque", safe_value(execution.get("at_risk_count"))],
                ["Actions bloquées", safe_value(execution.get("blocked_count"))],
                ["Lots critiques", safe_value(execution.get("critical_lots_count"))],
                ["Livraisons à surveiller", safe_value(execution.get("deliveries_to_watch_count"))],
                ["ETA à surveiller", safe_value(execution.get("eta_to_watch_count"))],
                ["Statut préparation chantier", execution.get("status", EMPTY_VALUE)],
            ],
            styles,
        ))
    else:
        elements.append(Paragraph("Aucune action chantier disponible.", styles["normal"]))
    if execution_rows:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("Actions chantier critiques / à risque", styles["small"]))
        table_rows = [
            [
                row.get("priority"),
                row.get("lot"),
                row.get("problem"),
                row.get("impact"),
                row.get("responsible_name"),
                format_date(row.get("due_date")),
                row.get("status"),
            ]
            for row in execution_rows[:20]
        ]
        elements.append(_build_table(["Priorité", "Lot", "Problème", "Impact", "Responsable", "Échéance", "Statut"], table_rows))
    else:
        elements.append(Paragraph("Aucune action chantier disponible.", styles["normal"]))
    elements.append(PageBreak())

    # Alerts
    elements.append(Paragraph("Alertes et risques", styles["section"]))
    alerts = _build_alerts(workflow)
    for alert in alerts:
        elements.append(Paragraph(f"[{alert['level'].upper()}] {alert['message']}", styles["normal"]))
        elements.append(Paragraph(f"Action recommandée : {alert['recommendation']}", styles["small"]))
    if not alerts:
        elements.append(Paragraph("Aucune alerte majeure détectée.", styles["normal"]))
    elements.append(PageBreak())

    # Workflow history
    elements.append(Paragraph("Historique workflow", styles["section"]))
    if events:
        table_rows = [
            [
                format_date(row.get("created_at")),
                row.get("event_type"),
                row.get("entity_type"),
                row.get("previous_status"),
                row.get("new_status"),
                row.get("message"),
                safe_value(row.get("user_id")),
            ]
            for row in events[:20]
        ]
        elements.append(_build_table(["Date", "Type", "Entité", "Ancien statut", "Nouveau statut", "Message", "Utilisateur"], table_rows))
    else:
        elements.append(Paragraph("Aucun événement workflow disponible pour le moment.", styles["normal"]))
    elements.append(PageBreak())

    # Conclusion
    elements.append(Paragraph("Conclusion / prochaine action", styles["section"]))
    elements.append(_build_key_value_table(
        [
            ["Statut global", workflow.get("label", EMPTY_VALUE)],
            ["Prochaine action recommandée", workflow.get("primary_action", {}).get("label", EMPTY_VALUE)],
            ["Responsable action", project.project_manager or EMPTY_VALUE],
            ["Remarque de fiabilité", safe_value(
                "Les données sont partielles et nécessitent une validation opérationnelle." if workflow.get("status") != "ACTIVE" else "Le projet dispose d’une base prête pour pilotage."
            )],
        ],
        styles,
    ))

    doc.build(elements, onFirstPage=_draw_page_number, onLaterPages=_draw_page_number)
    buffer.seek(0)
    return buffer
