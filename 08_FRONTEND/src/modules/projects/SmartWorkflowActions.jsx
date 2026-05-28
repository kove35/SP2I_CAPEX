import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Circle,
  ClipboardCheck,
  Coins,
  PackageCheck,
  Route,
  ShieldCheck,
  ShoppingCart,
  Truck,
  XCircle,
} from "lucide-react";

function money(value) {
  const amount = Number(value || 0);
  if (!Number.isFinite(amount) || amount <= 0) return "-";
  return `${amount.toLocaleString("fr-FR", { maximumFractionDigits: 0 })} FCFA`;
}

function count(value) {
  return Number(value || 0).toLocaleString("fr-FR");
}

function stepById(workflow, id) {
  return workflow?.steps?.find((step) => step.id === id) || {};
}

function currentStep(workflow) {
  return workflow?.active_step || workflow?.steps?.find((step) => ["blocking", "todo", "progress"].includes(step.state)) || workflow?.steps?.at?.(-1) || {};
}

function nextStepLabel(workflow) {
  if (workflow?.next_action?.label) return workflow.next_action.label;
  const step = currentStep(workflow);
  if (step.id === "scenarios") return "Arbitrage procurement";
  if (step.id === "procurement") return "Validation humaine des décisions achat";
  if (step.id === "execution") return "Préparation chantier et ETA";
  if (step.id === "budget") return "Simulation CAPEX";
  if (step.id === "dqe") return "Synchronisation budget";
  return step.label || workflow?.label || "Pilotage projet";
}

const timelineIcons = {
  done: CheckCircle2,
  active: Route,
  waiting: Circle,
  blocked: XCircle,
  risk: AlertTriangle,
};

function formatWorkflowState(value) {
  return String(value || "WORKFLOW")
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/^\w/, (letter) => letter.toUpperCase());
}

function buildActions({ workflow = {}, module = "dashboard", kpis = {}, simulation = null, execution = {}, procurement = {} }) {
  const scenarioDone = stepById(workflow, "scenarios").state === "done" || workflow?.scenario?.is_ready || simulation;
  const procurementStatus = workflow?.procurement?.status || procurement.status;
  const procurementReady = workflow?.procurement?.is_ready || ["READY", "EXPORTABLE"].includes(procurementStatus);
  const executionStatus = workflow?.execution?.status || execution.status;
  const gain = Number(simulation?.kpi?.economie_nette || kpis.economie_nette || kpis.gainSecurisable || kpis.gain_net_total || 0);
  const lines = Number(simulation?.kpi?.lignes_importables || workflow?.procurement?.decisions_count || procurement.decisions_count || kpis.nb_lignes || 0);
  const validations = Number(workflow?.procurement?.review_required_count || workflow?.procurement?.to_arbitrate_count || procurement.review_required_count || 0);
  const criticalLots = Number(workflow?.execution?.critical_lots_count || execution.critical_lots_count || execution.blockedLots || 0);
  const etaWatch = Number(workflow?.execution?.eta_to_watch_count || execution.eta_to_watch_count || 0);

  if (!scenarioDone) {
    return [
      {
        role: "Direction",
        title: "Simuler la stratégie CAPEX",
        route: "/app/simulation",
        tone: "opportunity",
        Icon: Coins,
        why: "Comparer local, import et hybride avant engagement achat.",
        impact: [`Gain estimé : ${money(gain)}`, `${count(lines)} lignes à analyser`, "Impact planning calculé après simulation"],
      },
      {
        role: "Logistique",
        title: "Vérifier paramètres logistiques",
        route: "/app/procurement?tab=containers",
        tone: "attention",
        Icon: Truck,
        why: "Contrôler douane, transport, ETA et consolidation container.",
        impact: ["Risque supply chain : à qualifier", "ETA import : à confirmer", "Prochaine étape : simulation CAPEX"],
      },
    ];
  }

  if (!procurementReady) {
    return [
      {
        role: "Procurement",
        title: "Analyser les arbitrages achat",
        route: "/app/procurement",
        tone: validations ? "critical" : "attention",
        Icon: ShoppingCart,
        why: "Transformer les recommandations import/local en décisions humaines traçables.",
        impact: [`${count(lines)} lignes importables ou arbitrables`, `Gain potentiel : ${money(gain)}`, `${count(validations)} validations humaines requises`, `${count(criticalLots)} lots critiques à arbitrer`],
      },
      {
        role: "Direction",
        title: "Approuver les économies CAPEX",
        route: "/app/approvals",
        tone: validations ? "critical" : "opportunity",
        Icon: ShieldCheck,
        why: "Sécuriser les économies avant commande fournisseur.",
        impact: [`Économies sécurisables : ${money(gain)}`, "Conséquence : dossier procurement direction", "Traçabilité : approval workflow"],
      },
      {
        role: "Logistique",
        title: "Préparer les consolidations container",
        route: "/app/procurement?tab=containers",
        tone: "opportunity",
        Icon: PackageCheck,
        why: "Regrouper les lots import compatibles et réduire les coûts de transport.",
        impact: ["Impact supply chain : FCL/LCL à confirmer", "Risque douane : à qualifier", "Prochaine étape : validation procurement"],
      },
    ];
  }

  if (executionStatus === "REQUIRED" || stepById(workflow, "execution").state === "todo") {
    return [
      {
        role: "Chantier",
        title: "Préparer les lots chantier",
        route: "/app/site?tab=planning",
        tone: criticalLots ? "attention" : "validated",
        Icon: ClipboardCheck,
        why: "Convertir les décisions achat validées en prérequis chantier.",
        impact: [`${count(criticalLots)} lots critiques`, `${count(etaWatch)} ETA à surveiller`, "Impact chantier : planning à sécuriser"],
      },
      {
        role: "Procurement",
        title: "Générer les commandes fournisseurs",
        route: "/app/procurement",
        tone: "validated",
        Icon: CheckCircle2,
        why: "Passer des arbitrages validés aux commandes opérationnelles.",
        impact: ["Statut validation : prêt", "Conséquence : lancement approvisionnement", `Gain sécurisé : ${money(gain)}`],
      },
    ];
  }

  return [
    {
      role: module === "execution" ? "Chantier" : "Direction",
      title: module === "execution" ? "Suivre les matériaux bloquants" : "Piloter les décisions CAPEX sécurisées",
      route: module === "execution" ? "/app/site?tab=deliveries" : "/app/analytics",
      tone: criticalLots ? "attention" : "validated",
      Icon: module === "execution" ? AlertTriangle : Route,
      why: "Maintenir le lien entre budget, commande, transport et préparation chantier.",
      impact: [`${count(criticalLots)} lots critiques`, `${count(etaWatch)} ETA à surveiller`, `Économies suivies : ${money(gain)}`],
    },
  ];
}

export default function SmartWorkflowActions({
  workflow,
  module = "dashboard",
  kpis = {},
  simulation = null,
  execution = {},
  procurement = {},
  onNavigate,
}) {
  const actions = buildActions({ workflow, module, kpis, simulation, execution, procurement });
  const current = currentStep(workflow);
  const timeline = workflow?.timeline || [];
  const metrics = workflow?.metrics || {};
  const blockers = workflow?.blockers || [];

  return (
    <section className="smart-workflow-actions" data-testid="smart-workflow-actions">
      <header>
        <div>
          <span>Copilote actions SP2I</span>
          <strong>Etat global : {workflow?.global_state_label || formatWorkflowState(workflow?.global_state || workflow?.status)}</strong>
          <small>Etape active : {current.label || "Pilotage projet"} · Action suivante : {nextStepLabel(workflow)}</small>
          {blockers.length ? (
            <div className="workflow-blocker-row" aria-label="Blocages workflow">
              {blockers.slice(0, 3).map((blocker) => (
                <b key={blocker.label} className={blocker.severity}>{blocker.label}</b>
              ))}
            </div>
          ) : null}
        </div>
        <ol className="smart-timeline" aria-label="Timeline opérationnelle">
          {(timeline.length ? timeline : ["Simulation", "Arbitrage", "Validation", "Commande", "Transport", "Reception", "Préparation Chantier"].map((label) => ({ label, state: "waiting" }))).map((item) => {
            const Icon = timelineIcons[item.state] || Circle;
            return (
              <li key={item.id || item.label} className={item.state}>
                <Icon size={14} />
                <span>{item.label}</span>
                <small>{item.metric}</small>
              </li>
            );
          })}
        </ol>
        <div className="workflow-live-metrics" aria-label="Indicateurs workflow">
          {[
            ["Progression", `${metrics.progress_percent ?? workflow?.completion ?? 0}%`],
            ["Lignes validees", count(metrics.validated_lines_count)],
            ["Commandes", count(metrics.orders_generated_count)],
            ["ETA moyen", metrics.average_eta_days ? `${metrics.average_eta_days} j` : "a confirmer"],
            ["Containers", count(metrics.active_containers_count)],
          ].map(([label, value]) => (
            <span key={label}><strong>{value}</strong>{label}</span>
          ))}
        </div>
      </header>
      <div className="smart-action-grid">
        {actions.map(({ Icon, ...action }) => (
          <button
            key={`${action.role}-${action.title}`}
            type="button"
            className={`smart-action-card ${action.tone}`}
            onClick={() => onNavigate?.(action.route)}
          >
            <span className="smart-action-role"><Icon size={16} /> {action.role}</span>
            <strong>{action.title}</strong>
            <p>{action.why}</p>
            <ul>
              {action.impact.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </button>
        ))}
      </div>
    </section>
  );
}
