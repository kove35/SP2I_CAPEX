from __future__ import annotations

from typing import Any

from app.workflow.schemas.workflow import WorkflowAction, WorkflowAlert, WorkflowBlocker


def compute_workflow_state(snapshot: dict[str, Any]) -> str:
    base = snapshot.get("base_metrics")
    procurement = snapshot.get("procurement") or {}
    execution = snapshot.get("execution") or {}
    setup_configured = bool(getattr(base, "setup_configured", False))
    sync_status = str(getattr(base, "sync_status", "OUT_OF_SYNC") or "OUT_OF_SYNC")
    dqe_ready = sync_status == "SYNCED"
    budget_synced = dqe_ready and bool(getattr(base, "capex_local_total", 0) > 0)
    simulation_ready = bool(getattr(base, "simulation_rows", 0) > 0)
    decisions = int(procurement.get("decisions_count") or 0)
    validated = int(procurement.get("validated_decisions_count") or 0)
    pending = sum(int(procurement.get(key) or 0) for key in ("pending_decisions_count", "to_arbitrate_count", "review_required_count", "blocked_decisions_count"))
    orders = int(snapshot.get("orders_count") or 0)
    containers = int(snapshot.get("containers_count") or 0)
    received = int(snapshot.get("received_count") or 0)
    actions = int(execution.get("actions_count") or 0)

    if not setup_configured:
        return "CONFIGURATION"
    if sync_status != "SYNCED":
        return "OUT_OF_SYNC"
    if not dqe_ready:
        return "DQE_CERTIFIED"
    if not budget_synced:
        return "BUDGET_SYNCED"
    if not simulation_ready:
        return "SIMULATION_READY"
    if decisions <= 0:
        return "SIMULATION_COMPLETED"
    if pending > 0 or validated < decisions:
        return "ARBITRAGE_IN_PROGRESS"
    if orders <= 0:
        return "ARBITRAGE_COMPLETED"
    if containers <= 0:
        return "ORDER_READY"
    if received <= 0:
        return "IN_TRANSIT"
    if actions <= 0:
        return "RECEIVED"
    if int(execution.get("done_count") or 0) >= actions:
        return "EXECUTION_COMPLETED"
    if actions > 0:
        return "CHANTIER_READY"
    return "CONFIGURATION"


def compute_active_step(workflow_state: str) -> str:
    return {
        "CONFIGURATION": "CONFIGURATION",
        "DQE_CERTIFIED": "DQE",
        "OUT_OF_SYNC": "DQE",
        "BUDGET_SYNCED": "BUDGET",
        "SIMULATION_READY": "SIMULATION",
        "SIMULATION_COMPLETED": "ARBITRAGE",
        "ARBITRAGE_IN_PROGRESS": "ARBITRAGE",
        "ARBITRAGE_COMPLETED": "VALIDATION",
        "PROCUREMENT_VALIDATED": "COMMANDE",
        "ORDER_READY": "COMMANDE",
        "ORDERED": "TRANSPORT",
        "IN_TRANSIT": "TRANSPORT",
        "RECEIVED": "RECEPTION",
        "CHANTIER_READY": "PREPARATION_CHANTIER",
        "EXECUTION_IN_PROGRESS": "EXECUTION",
        "EXECUTION_COMPLETED": "CLOTURE",
    }.get(workflow_state, "CONFIGURATION")


def compute_next_action(workflow_state: str, metrics) -> WorkflowAction:
    action_map = {
        "CONFIGURATION": WorkflowAction(label="Configurer le projet", route="/app/projects", reason="Le projet doit etre configure."),
        "DQE_CERTIFIED": WorkflowAction(label="Importer et certifier le DQE", route="/app/dqe?tab=import"),
        "OUT_OF_SYNC": WorkflowAction(label="Resynchroniser le DQE", route="/app/dqe?tab=sync", reason="Le DQE certifie actif et FACT_METRE sont divergents."),
        "BUDGET_SYNCED": WorkflowAction(label="Synchroniser le budget CAPEX", route="/app/dqe?tab=sync"),
        "SIMULATION_READY": WorkflowAction(label="Simuler la strategie CAPEX", route="/app/simulation"),
        "SIMULATION_COMPLETED": WorkflowAction(label="Analyser les arbitrages achat", route="/app/procurement"),
        "ARBITRAGE_IN_PROGRESS": WorkflowAction(label="Valider les decisions import critiques", route="/app/procurement"),
        "ARBITRAGE_COMPLETED": WorkflowAction(label="Generer les commandes fournisseurs", route="/app/procurement"),
        "PROCUREMENT_VALIDATED": WorkflowAction(label="Generer les commandes fournisseurs", route="/app/procurement"),
        "ORDER_READY": WorkflowAction(label="Valider les commandes fournisseurs", route="/app/procurement"),
        "ORDERED": WorkflowAction(label="Preparer les containers import", route="/app/approvisionnement"),
        "IN_TRANSIT": WorkflowAction(label="Confirmer les ETA fournisseurs", route="/app/approvisionnement"),
        "RECEIVED": WorkflowAction(label="Preparer les lots chantier", route="/app/site?tab=planning"),
        "CHANTIER_READY": WorkflowAction(label="Preparer les equipes chantier", route="/app/site?tab=planning"),
        "EXECUTION_IN_PROGRESS": WorkflowAction(label="Piloter la preparation chantier", route="/app/site?tab=planning"),
        "EXECUTION_COMPLETED": WorkflowAction(label="Cloturer le projet", route="/app/projects"),
    }
    if metrics.execution_blocked:
        return WorkflowAction(label="Debloquer le lot critique", route="/app/site?tab=planning", reason="Des lots chantier sont bloques.")
    return action_map.get(workflow_state, action_map["CONFIGURATION"])


def compute_blockers(workflow_state: str, snapshot: dict[str, Any], metrics) -> list[WorkflowBlocker]:
    blockers: list[WorkflowBlocker] = []
    if workflow_state == "OUT_OF_SYNC":
        blockers.append(WorkflowBlocker(code="DQE_OUT_OF_SYNC", label="Le DQE certifie actif est hors synchronisation avec FACT_METRE.", severity="critical", module="dqe"))
    if workflow_state == "ARBITRAGE_IN_PROGRESS" and metrics.pending_lines:
        blockers.append(WorkflowBlocker(code="ARBITRAGE_INCOMPLETE", label="Arbitrage achat incomplet", module="procurement"))
    if metrics.execution_blocked:
        blockers.append(WorkflowBlocker(code="CHANTIER_LOT_BLOCKED", label="Lot chantier dependant ou bloque", severity="critical", module="site"))
    if metrics.eta_average_days >= 60:
        blockers.append(WorkflowBlocker(code="ETA_CRITICAL", label="ETA critique", severity="warning", module="logistics"))
    if snapshot.get("supplier_unconfirmed_count"):
        blockers.append(WorkflowBlocker(code="SUPPLIER_UNCONFIRMED", label="Fournisseur non confirme", module="procurement"))
    return blockers


def compute_alerts(workflow_state: str, metrics, blockers: list[WorkflowBlocker]) -> list[WorkflowAlert]:
    alerts = [WorkflowAlert(code=blocker.code, message=blocker.label, severity=blocker.severity, module=blocker.module) for blocker in blockers]
    if workflow_state == "ARBITRAGE_COMPLETED" and metrics.orders <= 0:
        alerts.append(WorkflowAlert(code="ORDER_MISSING", message="Commandes fournisseurs a generer.", severity="info", module="procurement"))
    return alerts
