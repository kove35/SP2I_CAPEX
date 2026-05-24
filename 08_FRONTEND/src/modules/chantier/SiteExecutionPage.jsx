import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import { useAppStore } from "../../store/appStore.jsx";
import { getScenarioContext, PROJECT_CONTEXT } from "../../utils/businessContext";
import { generateProjectExecutionActions, getProjectWorkflow, listProjectExecutionActions } from "../../services/projectService";
import WorkflowGuardEmptyState from "../projects/WorkflowGuardEmptyState";

const DQE_READY_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];

const siteActions = [
  {
    priority: "Haute",
    lot: "L01 - Gros oeuvre et demolition",
    issue: "Arbitrage import/local a securiser",
    impact: "Chemin critique",
    owner: "Responsable chantier + achat",
    due: "Cette semaine",
    status: "À traiter",
  },
  {
    priority: "Moyenne",
    lot: "L07 - Electricite",
    issue: "Livraison fournisseur a confirmer",
    impact: "Risque planning moyen",
    owner: "Responsable achat",
    due: "7 jours",
    status: "À surveiller",
  },
  {
    priority: "Moyenne",
    lot: "Menuiserie aluminium",
    issue: "Stockage et sequence de pose a consolider",
    impact: "Risque de saturation site",
    owner: "Conducteur travaux",
    due: "Prochaine reunion chantier",
    status: "À planifier",
  },
];

const deliveries = [
  { delivery: "Tableaux et accessoires electriques", lot: "Electricite", supplier: "Fournisseur a confirmer", eta: "14 j", need: "10 j", gap: "+4 j", risk: "Moyen", action: "Confirmer fournisseur ou alternative locale" },
  { delivery: "Equipements plomberie", lot: "Plomberie", supplier: "Sourcing local/import", eta: "21 j", need: "18 j", gap: "+3 j", risk: "Moyen", action: "Securiser livraison et stockage" },
  { delivery: "Menuiseries aluminium", lot: "Menuiserie", supplier: "Fournisseur a valider", eta: "35 j", need: "25 j", gap: "+10 j", risk: "Eleve", action: "Arbitrage achat requis" },
];

const dependencies = [
  { upstream: "Gros oeuvre", downstream: "Electricite", type: "Reservations / passages reseaux", need: "A confirmer", risk: "Moyen", action: "Valider planning d'intervention" },
  { upstream: "Menuiserie", downstream: "Finitions", type: "Fermeture batiment", need: "A confirmer", risk: "Eleve", action: "Securiser livraison menuiserie" },
  { upstream: "Plomberie", downstream: "Revetements", type: "Essais reseaux avant fermeture", need: "A confirmer", risk: "Moyen", action: "Programmer controle technique" },
];

const planningRows = [
  { lot: "L01 - Gros oeuvre", start: "-", required: "-", eta: "-", gap: "-", status: "À compléter" },
  { lot: "L07 - Electricite", start: "-", required: "10 j", eta: "14 j", gap: "+4 j", status: "À surveiller" },
  { lot: "Menuiserie aluminium", start: "-", required: "25 j", eta: "35 j", gap: "+10 j", status: "Critique" },
];

const criticalAlerts = [
  { lot: "Menuiserie aluminium", exposedBudget: "Eleve", drift: "Forte", action: "Remonter arbitrage achat + planning" },
  { lot: "Electricite", exposedBudget: "Moyen", drift: "Moyenne", action: "Confirmer delai fournisseur" },
  { lot: "Gros oeuvre", exposedBudget: "Eleve", drift: "Faible", action: "Verifier dependances chantier" },
];

function readDqeVersions(projectId) {
  try {
    const stored = window.localStorage.getItem(`sp2i:dqeVersions:${projectId || PROJECT_CONTEXT.code}`);
    if (stored) {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed : [];
    }
  } catch {
    return [];
  }

  if ((projectId || PROJECT_CONTEXT.code) === PROJECT_CONTEXT.code) {
    return [{
      version_number: 1,
      status: "SYNCED",
      trust_score: 87,
      normalized_lines_count: 46,
      data_loss_count: 0,
      review_required_count: 0,
      is_active: true,
    }];
  }
  return [];
}

function getExecutionContext(projectId, scenarioCode, lastSimulation) {
  const activeDqe = readDqeVersions(projectId).find((version) => version.is_active && DQE_READY_STATUSES.includes(version.status));
  const scenario = getScenarioContext(scenarioCode);
  return {
    hasActiveDqe: Boolean(activeDqe),
    dqeLabel: activeDqe ? `DQE v${activeDqe.version_number}` : "Aucun DQE actif",
    dqeStatus: activeDqe?.status === "CERTIFIED" ? "Certifié" : activeDqe?.status === "CERTIFIED_WITH_WARNINGS" ? "Certifié avec points à vérifier" : activeDqe?.status === "SYNCED" ? "Synchronisé" : "Non disponible",
    trustScore: activeDqe?.trust_score,
    lines: activeDqe?.normalized_lines_count,
    dataLoss: activeDqe?.data_loss_count,
    reviewRequired: activeDqe?.review_required_count,
    scenarioLabel: scenario.label,
    scenarioStatus: lastSimulation ? "Simule" : "A lancer",
    globalRisk: lastSimulation ? "Moyen" : "À évaluer",
  };
}

function navigate(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function DataTable({ columns, rows, empty }) {
  return (
    <div className="data-table-wrap panel-scroll">
      <table className="data-table">
        <thead>
          <tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.lot || row.delivery || row.upstream || "row"}-${index}`}>
              {columns.map((column) => <td key={column.key}>{row[column.key] || "-"}</td>)}
            </tr>
          ))}
          {!rows.length ? <tr><td colSpan={columns.length}>{empty}</td></tr> : null}
        </tbody>
      </table>
    </div>
  );
}

function mapExecutionAction(action) {
  const priorityLabels = { LOW: "Basse", MEDIUM: "Moyenne", HIGH: "Haute", CRITICAL: "Critique" };
  const statusLabels = {
    TO_DO: "À traiter",
    IN_PROGRESS: "En cours",
    DONE: "Terminé",
    AT_RISK: "À risque",
    BLOCKED: "Bloqué",
    CANCELLED: "Annulé",
  };
  return {
    priority: priorityLabels[action.priority] || action.priority || "Moyenne",
    lot: action.lot || action.family || "-",
    issue: action.problem || action.title || "Action chantier à planifier",
    impact: action.impact || "-",
    owner: action.responsible_name || action.responsible_role || "Responsable chantier",
    due: action.due_date ? new Date(action.due_date).toLocaleDateString("fr-FR") : "À planifier",
    status: statusLabels[action.status] || action.status || "À traiter",
  };
}

export default function SiteExecutionPage() {
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "planning");
  const [remoteActions, setRemoteActions] = React.useState([]);
  const { state } = useAppStore();
  const workflow = React.useMemo(
    () => getProjectWorkflow(state.activeProjectDetails || { id: state.activeProject, workspace_key: state.activeProject }, state),
    [state]
  );
  const setupDone = workflow.steps.find((step) => step.id === "configuration")?.state === "done";
  const procurementReady = workflow.procurement?.is_ready || workflow.steps.find((step) => step.id === "procurement")?.state === "done";
  const executionStatus = workflow.execution?.status || "BLOCKED";
  const executionReady = workflow.execution?.is_ready || workflow.steps.find((step) => step.id === "execution")?.state === "done";
  const executionSummary = workflow.execution || {};
  const context = React.useMemo(
    () => getExecutionContext(state.activeProject || PROJECT_CONTEXT.code, state.activeScenario, state.lastSimulation),
    [state.activeProject, state.activeScenario, state.lastSimulation]
  );

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "planning");
  }, [window.location.search]);

  React.useEffect(() => {
    let cancelled = false;
    listProjectExecutionActions(state.activeProject, workflow.scenario?.scenario_id).then((payload) => {
      if (!cancelled && Array.isArray(payload?.actions)) {
        setRemoteActions(payload.actions.map(mapExecutionAction));
      }
    });
    return () => {
      cancelled = true;
    };
  }, [state.activeProject, workflow.scenario?.scenario_id]);

  const handleGenerateExecutionActions = async () => {
    await generateProjectExecutionActions(state.activeProject, workflow.scenario?.scenario_id);
    const payload = await listProjectExecutionActions(state.activeProject, workflow.scenario?.scenario_id);
    if (Array.isArray(payload?.actions)) {
      setRemoteActions(payload.actions.map(mapExecutionAction));
    }
  };

  const storageUsed = 72;
  const storageRemaining = 100 - storageUsed;
  const displayedActions = remoteActions.length ? remoteActions : siteActions;
  const blockedLots = Number(executionSummary.critical_lots_count || 0) || displayedActions.filter((action) => action.priority === "Haute" || action.priority === "Critique").length;
  const criticalDeliveries = deliveries.filter((item) => item.risk === "Eleve" || item.risk === "Moyen").length;
  const watchedEta = deliveries.filter((item) => String(item.gap).startsWith("+")).length;

  const tabContent = {
    planning: {
      title: "Planning operationnel",
      help: "Relier les livraisons attendues aux besoins chantier sans inventer de dates non certifiees.",
      columns: [
        { key: "lot", label: "Lot" },
        { key: "start", label: "Debut prevu" },
        { key: "required", label: "Livraison requise" },
        { key: "eta", label: "ETA estime" },
        { key: "gap", label: "Ecart" },
        { key: "status", label: "Statut" },
      ],
      rows: planningRows,
      empty: "Aucune ligne planning disponible.",
    },
    dependencies: {
      title: "Dependances chantier",
      help: "Identifier les liens entre lots pour eviter qu'un arbitrage achat ne bloque une intervention terrain.",
      columns: [
        { key: "upstream", label: "Lot amont" },
        { key: "downstream", label: "Lot dependant" },
        { key: "type", label: "Type de dependance" },
        { key: "need", label: "Date besoin" },
        { key: "risk", label: "Risque" },
        { key: "action", label: "Action" },
      ],
      rows: dependencies,
      empty: "Aucune dependance critique identifiee.",
    },
    deliveries: {
      title: "Livraisons critiques",
      help: "Suivre les ETA qui peuvent creer un ecart avec le besoin chantier.",
      columns: [
        { key: "delivery", label: "Livraison" },
        { key: "lot", label: "Lot" },
        { key: "supplier", label: "Fournisseur" },
        { key: "eta", label: "ETA" },
        { key: "need", label: "Besoin chantier" },
        { key: "gap", label: "Ecart" },
        { key: "risk", label: "Risque" },
        { key: "action", label: "Action" },
      ],
      rows: deliveries,
      empty: "Aucune livraison critique identifiee.",
    },
    criticality: {
      title: "Alertes operationnelles",
      help: "Les lots critiques combinent budget expose, derive possible et impact planning.",
      columns: [
        { key: "lot", label: "Lot" },
        { key: "exposedBudget", label: "Budget expose" },
        { key: "drift", label: "Probabilite de derive" },
        { key: "action", label: "Action chantier" },
      ],
      rows: criticalAlerts,
      empty: "Aucune alerte chantier critique identifiee.",
    },
  };
  const activeTab = tabContent[tab] || tabContent.planning;

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">Pilotage chantier</p>
        <h1>Planning, dependances, livraisons et stockage chantier</h1>
        <p>Piloter les priorités chantier liées aux décisions CAPEX, aux livraisons et aux risques d’exécution.</p>
      </section>

      <section className={`execution-context-strip ${context.hasActiveDqe ? "ready" : "blocked"}`}>
        <div>
          <strong>{context.dqeLabel}</strong>
          <span>{context.hasActiveDqe ? `${context.dqeStatus} · Trust score ${context.trustScore ?? "-"}/100 · ${context.lines ?? "-"} lignes` : "Importez et validez un DQE avant de piloter l’exécution chantier."}</span>
        </div>
        <div>
          <strong>Scénario actif : {context.scenarioLabel}</strong>
          <span>{context.scenarioStatus} · impact planning {context.scenarioStatus === "Simule" ? "à surveiller" : "non calculé"}</span>
        </div>
        <div>
          <strong>Gouvernance</strong>
          <span>{context.hasActiveDqe ? `${context.dataLoss ?? 0} perte stricte · ${context.reviewRequired ?? 0} validation bloquante` : "Validation requise"}</span>
        </div>
        <div>
          <strong>Risque global</strong>
          <span>{context.globalRisk}</span>
        </div>
      </section>

      {!setupDone ? (
        <WorkflowGuardEmptyState
          title="Configuration projet requise"
          message="Ce projet doit etre configure avant de poursuivre le workflow CAPEX."
          actionLabel="Configurer le projet"
          actionRoute="/app/projects"
          severity="blocking"
          currentStep={workflow.label}
          requiredStep="Configuration projet"
          testId="execution-empty-state"
        />
      ) : !procurementReady ? (
        <WorkflowGuardEmptyState
          title="Approvisionnement à préparer"
          message="Préparez les arbitrages achat avant de suivre l’exécution chantier."
          actionLabel="Ouvrir Approvisionnement"
          actionRoute="/app/procurement"
          currentStep={workflow.steps.find((step) => step.id === "procurement")?.status}
          requiredStep="Approvisionnement"
          testId="execution-empty-state"
        />
      ) : !executionReady && executionStatus === "REQUIRED" ? (
        <div>
        <WorkflowGuardEmptyState
          title="Exécution à préparer"
          message="L’approvisionnement est prêt. Préparez les actions chantier avant le suivi opérationnel."
          actionLabel="Préparer l’exécution"
          actionRoute="/app/site?tab=planning"
          currentStep={workflow.steps.find((step) => step.id === "execution")?.status}
          requiredStep="Actions chantier"
          testId="execution-empty-state"
        />
        <button type="button" className="primary-action secondary-action" onClick={handleGenerateExecutionActions}>
          Générer actions chantier
        </button>
        </div>
      ) : null}

      {setupDone && !context.hasActiveDqe ? (
        <div className="app-warning">
          Aucun DQE actif. Importez et validez un DQE avant de piloter l’exécution chantier.
          <button type="button" className="link-button" onClick={() => navigate("/app/dqe?tab=import")}> Importer un DQE</button>
        </div>
      ) : null}
      {setupDone && !state.lastSimulation ? (
        <div className="app-warning">
          Aucun scénario actif. Lancez une simulation pour estimer l’impact planning.
          <button type="button" className="link-button" onClick={() => navigate("/app/simulation")}> Tester un scénario</button>
        </div>
      ) : null}

      <div className="tab-row">
        <button className={tab === "planning" ? "active" : ""} onClick={() => setTab("planning")} type="button">Planning</button>
        <button className={tab === "dependencies" ? "active" : ""} onClick={() => setTab("dependencies")} type="button">Dependances</button>
        <button className={tab === "deliveries" ? "active" : ""} onClick={() => setTab("deliveries")} type="button">Livraisons</button>
        <button className={tab === "criticality" ? "active" : ""} onClick={() => setTab("criticality")} type="button">Alertes critiques</button>
      </div>

      <section className="metric-grid">
        <KpiCard label="Lots critiques" value={blockedLots} tone="warning" />
        <KpiCard label="Livraisons à risque" value={Number(executionSummary.deliveries_to_watch_count || 0) || criticalDeliveries} tone="warning" />
        <KpiCard label="Stockage utilise" value={`${storageUsed}%`} />
        <KpiCard label="ETA à surveiller" value={Number(executionSummary.eta_to_watch_count || 0) || watchedEta} />
        <KpiCard label="Budget expose" value="A consolider" />
        <KpiCard label="Actions requises" value={Number(executionSummary.actions_count || 0) || displayedActions.length} tone="warning" />
      </section>

      <section className="procurement-scope-note" data-testid="execution-actions-summary">
        <span>Actions chantier : {Number(executionSummary.actions_count || displayedActions.length || 0).toLocaleString("fr-FR")}</span>
        <span>Ouvertes : {Number(executionSummary.open_count || 0).toLocaleString("fr-FR")}</span>
        <span>Terminées : {Number(executionSummary.done_count || 0).toLocaleString("fr-FR")}</span>
        <span>À risque : {Number(executionSummary.at_risk_count || 0).toLocaleString("fr-FR")}</span>
        <span>Bloquées : {Number(executionSummary.blocked_count || 0).toLocaleString("fr-FR")}</span>
        <span>Source : {executionSummary.source || "fact_simulation"}</span>
      </section>

      <section className="execution-operational-grid">
        <AnalyticsCard title="Actions chantier prioritaires" eyebrow="Priorites operationnelles">
          <DataTable
            columns={[
              { key: "priority", label: "Priorite" },
              { key: "lot", label: "Lot" },
              { key: "issue", label: "Probleme" },
              { key: "impact", label: "Impact chantier" },
              { key: "owner", label: "Responsable" },
              { key: "due", label: "Echeance" },
              { key: "status", label: "Statut" },
            ]}
            rows={displayedActions}
            empty="Aucune action chantier critique identifiee pour le moment."
          />
        </AnalyticsCard>
        <AnalyticsCard title="Stockage site" eyebrow="Capacite chantier">
          <div className="execution-storage-card">
            <strong>{storageUsed}% utilise</strong>
            <div className="procurement-progress"><i style={{ width: `${storageUsed}%` }} /></div>
            <ul className="signal-list">
              <li>Seuil de surveillance : 70%.</li>
              <li>Seuil critique : 80%.</li>
              <li>Capacite restante : {storageRemaining}%.</li>
              <li>Risque : moyen.</li>
              <li>Action : prioriser les livraisons par lot et eviter les arrivees simultanees.</li>
            </ul>
          </div>
        </AnalyticsCard>
      </section>

      <section className="cockpit-split">
        <AnalyticsCard title={activeTab.title} eyebrow="Suivi operationnel">
          <p className="execution-help">{activeTab.help}</p>
          <DataTable columns={activeTab.columns} rows={activeTab.rows} empty={activeTab.empty} />
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Impact approvisionnement" eyebrow="Lien achat / chantier">
            <ul className="signal-list">
              <li>Source approvisionnement : scénario {context.scenarioLabel}.</li>
              <li>Lignes import : a consolider depuis le workbench achat.</li>
              <li>Lignes hybrides : a arbitrer avec le responsable chantier.</li>
              <li>ETA moyen import : a confirmer par fournisseur.</li>
              <li>Risque logistique : moyen tant que les containers ne sont pas consolides.</li>
            </ul>
            <button type="button" className="primary-action secondary-action" onClick={() => navigate("/app/procurement")}>
              Ouvrir Approvisionnement
            </button>
          </AnalyticsCard>
          <AnalyticsCard title="Alertes chantier à remonter" eyebrow="Risque exécution">
            <ul className="signal-list">
              <li>Lot bloque : L01 - Gros oeuvre et demolition, cause arbitrage achat a securiser.</li>
              <li>Livraison critique : Menuiserie aluminium, ecart ETA +10 jours.</li>
              <li>Stockage sous surveillance : 72% utilise, seuil critique 80%.</li>
              <li>Action suivante : arbitrer les lots critiques en reunion chantier + achat.</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
