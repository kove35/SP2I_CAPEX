import React from "react";
import CapexHeatmap from "../../components/charts/CapexHeatmap";
import CapexTimeline from "../../components/charts/CapexTimeline";
import CapexWaterfall from "../../components/charts/CapexWaterfall";
import ImportDecisionSankey from "../../components/charts/ImportDecisionSankey";
import RiskMatrix from "../../components/charts/RiskMatrix";
import GlobalAnalyticsFilters from "../../components/filters/GlobalAnalyticsFilters";
import FactMetreGrid from "../../components/grids/FactMetreGrid";
import InsightsPanel from "../../components/analytics/InsightsPanel";
import EnterpriseKpiGrid from "../../components/kpi/EnterpriseKpiGrid";
import { useAnalyticsEngine } from "../../hooks/useAnalyticsEngine";
import { useWorkflow } from "../../hooks/useWorkflow";
import ProjectQuickActions from "../../components/ProjectQuickActions";
import ProjectWorkflowStepper from "../projects/ProjectWorkflowStepper";
import SmartWorkflowActions from "../projects/SmartWorkflowActions";
import { useAppStore } from "../../store/appStore.jsx";
import { demoProjects, getProjectPrimaryAction, getProjectWorkspaceKey } from "../../services/projectService";
import { getScenarioContext } from "../../utils/businessContext";
import AnalyticsCard from "../../ui/AnalyticsCard";
import Skeleton from "../../ui/Skeleton";
import { formatMoney } from "../../shared/formatters";
import { buildApiUrl } from "../../services/apiClient";

function navigateTo(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function getWorkspaceProject(state) {
  if (state.activeProjectDetails) return state.activeProjectDetails;
  return demoProjects.find((project) => getProjectWorkspaceKey(project) === state.activeProject) || demoProjects[0];
}

function getStep(workflow, id) {
  return workflow.steps.find((step) => step.id === id) || {};
}

function buildProjectAlerts(workflow) {
  const alerts = [];
  const configuration = getStep(workflow, "configuration");
  const dqe = getStep(workflow, "dqe");
  const budget = getStep(workflow, "budget");
  const scenarios = getStep(workflow, "scenarios");
  const procurement = getStep(workflow, "procurement");
  const budgetStatus = workflow?.budget?.status;

  if (configuration.state !== "done") alerts.push("Ce projet doit etre configure avant de demarrer le workflow CAPEX.");
  if (dqe.state !== "done") alerts.push("Aucun DQE actif certifie. Importez un DQE pour analyser le budget du projet.");
  if (dqe.state === "done" && budget.state !== "done") {
    if (budgetStatus === "SYNC_FAILED") {
      alerts.push("La synchronisation du budget a echoue. Relancez la synchronisation.");
    } else if (budgetStatus === "PARTIAL_SYNC") {
      alerts.push("La synchronisation du budget est partielle. Verifiez la synchronisation avant de lancer les scenarios.");
    } else {
      alerts.push("Le DQE est certifie. Synchronisez le budget pour debloquer les scenarios.");
    }
  }
  if (budget.state === "done" && scenarios.state !== "done") alerts.push("Le budget est pret. Lancez une simulation pour comparer les strategies CAPEX.");
  if (scenarios.state === "done" && procurement.state !== "done") alerts.push("Un scénario est disponible. Préparez l’approvisionnement.");
  return alerts.length ? alerts : ["Projet actif. Les principaux modules sont disponibles pour pilotage."];
}

function buildFilterLabel(filters = {}) {
  const parts = [
    filters.batiment,
    filters.niveau,
    filters.lot,
    filters.famille,
    filters.importLocal || filters.decisionImport,
  ].filter(Boolean);
  return parts.length ? parts.join(" / ") : "Tous les filtres";
}

function formatDqeDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

function hasDqeReference(dqe = {}) {
  if ((dqe.status === "NOT_IMPORTED" || dqe.is_active === false) && !dqe.file_name) return false;
  return Boolean(
    dqe.file_name ||
    dqe.version_number ||
    dqe.uploaded_at ||
    dqe.synced_at ||
    dqe.is_active
  );
}

function isImportedDqeName(value) {
  return Boolean(value && !/a importer|à importer|aucun/i.test(value));
}

function resolveActiveDqe(workflow = {}, project = {}) {
  const candidates = [workflow.dqe, workflow.activeDqe, project.activeDqe, project.active_dqe]
    .filter(Boolean)
    .filter(hasDqeReference);
  const active = candidates.find((candidate) => candidate.is_active !== false) || candidates[0] || null;

  if (active?.file_name) return active;

  if (isImportedDqeName(project.last_dqe)) {
    return {
      ...(active || {}),
      file_name: project.last_dqe,
      version_number: active?.version_number || 1,
      trust_score: active?.trust_score ?? project.trust_score,
      uploaded_at: active?.uploaded_at || active?.synced_at,
      is_active: true,
    };
  }

  return active;
}

function moduleTone(state) {
  if (state === "done") return "ready";
  if (state === "progress" || state === "todo") return "pending";
  return "blocked";
}

function formatPercentValue(value) {
  const number = Number(value || 0);
  return `${(number * 100).toLocaleString("fr-FR", { maximumFractionDigits: 1 })}%`;
}

function firstItem(...collections) {
  for (const collection of collections) {
    if (Array.isArray(collection) && collection.length) return collection[0];
  }
  return null;
}

function qualityLabel(score = 0, reviewRequired = 0, status = "") {
  const value = Number(score || 0);
  if (reviewRequired > 0 || /WARN|REVIEW|BLOCK/i.test(status)) return value >= 75 ? "Bon" : "Moyen";
  if (value >= 90) return "Excellent";
  if (value >= 75) return "Bon";
  if (value >= 55) return "Moyen";
  return "Faible";
}

function buildCostSignals(costPayload = {}) {
  const topCosts = costPayload.top_costs || {};
  const capexM2 = costPayload.capex_m2 || {};
  const benchmark = costPayload.benchmark || {};
  const pareto = costPayload.pareto || {};
  const anomalies = costPayload.anomalies?.items || [];
  const piece = topCosts.pieces?.[0];
  const lot = topCosts.lots?.[0];
  const appartement = firstItem(topCosts.appartements, benchmark.appartements?.all, benchmark.appartements?.A101_A201_A301);
  const niveau = firstItem(topCosts.niveaux, capexM2.niveaux);
  const capexM2Piece = firstItem(capexM2.pieces, capexM2.appartements, capexM2.niveaux);
  const paretoArticle = firstItem(pareto.articles);
  const benchmarkPiece = firstItem(benchmark.pieces?.chambres, benchmark.pieces?.sdb);
  const saving = topCosts.economies?.[0];
  const anomaly = anomalies[0];
  const signals = [];

  if (capexM2Piece) {
    signals.push({
      label: "CAPEX / m2",
      value: capexM2Piece.scope || capexM2Piece.piece || capexM2Piece.appartement || "-",
      detail: formatMoney(capexM2Piece.capex_m2),
    });
  }

  if (piece) {
    signals.push({
      label: "Piece la plus couteuse",
      value: piece.label || piece.scope || "-",
      detail: formatMoney(piece.capex_optimise || piece.capex),
    });
  }
  if (lot) {
    signals.push({
      label: "Lot le plus couteux",
      value: lot.label || lot.scope || "-",
      detail: `${formatMoney(lot.capex_optimise || lot.capex)} - ROI ${formatPercentValue(lot.roi)}`,
    });
  }
  if (appartement) {
    signals.push({
      label: "Top appartement",
      value: appartement.label || appartement.appartement || appartement.scope || "-",
      detail: formatMoney(appartement.capex_optimise || appartement.capex),
    });
  }
  if (niveau) {
    signals.push({
      label: "Top niveau",
      value: niveau.label || niveau.scope || [niveau.batiment, niveau.niveau].filter(Boolean).join(" / ") || "-",
      detail: formatMoney(niveau.capex_optimise || niveau.capex),
    });
  }
  if (paretoArticle) {
    signals.push({
      label: "Pareto CAPEX",
      value: paretoArticle.article || paretoArticle.label || "-",
      detail: `${formatPercentValue(paretoArticle.cumulative_pct || paretoArticle.cumulative_share || paretoArticle.share)} du CAPEX`,
    });
  }
  if (benchmarkPiece) {
    signals.push({
      label: "Benchmark pieces",
      value: benchmarkPiece.piece || benchmarkPiece.label || "-",
      detail: `Moyenne ${formatMoney(benchmarkPiece.capex_moyen || benchmarkPiece.avg_capex || benchmarkPiece.capex_optimise)}`,
    });
  }
  if (saving) {
    signals.push({
      label: "Top economie",
      value: saving.label || saving.article || "-",
      detail: formatMoney(saving.economie),
    });
  }
  if (anomaly) {
    signals.push({
      label: "Anomalie detectee",
      value: [anomaly.appartement, anomaly.piece].filter(Boolean).join(" / ") || anomaly.article || "-",
      detail: `${anomaly.motif || "CAPEX/m2"} - ${formatMoney(anomaly.capex_optimise || anomaly.capex)}`,
    });
  } else if (costPayload.anomalies) {
    signals.push({
      label: "Anomalies detectees",
      value: "Aucune anomalie critique",
      detail: "CAPEX/m2 dans les seuils",
    });
  }

  return signals;
}

function buildDataQualitySignal(payload = {}) {
  const kpis = payload.kpis || {};
  const metadata = payload.metadata || {};
  const score = Number(kpis.trust_score ?? kpis.score_qualite ?? 0);
  const reviewRequired = Number(kpis.lignes_review_required || 0);
  return {
    label: "Qualite des donnees",
    value: qualityLabel(score, reviewRequired, metadata.qa_status),
    detail: `Trust Score ${Math.round(score || 0)}/100 - revue ${reviewRequired}`,
  };
}

export default function CockpitPage() {
  const { state } = useAppStore();
  const engine = useAnalyticsEngine("direction");
  const project = getWorkspaceProject(state);
  const projectKey = getProjectWorkspaceKey(project);
  const currentSimulation = state.lastSimulationProject === projectKey ? state.lastSimulation : null;
  const { workflow } = useWorkflow(project?.id || projectKey, project);
  const primaryAction = getProjectPrimaryAction({ ...project, backendWorkflow: workflow }, state);
  const alerts = buildProjectAlerts(workflow);
  const activeDqe = resolveActiveDqe(workflow, project);
  const activeDqeDownloadUrl = activeDqe ? buildApiUrl("/dqe/download-active") : "";
  const scenario = getScenarioContext(state.activeScenario);
  const dqeStep = getStep(workflow, "dqe");
  const budgetStep = getStep(workflow, "budget");
  const scenarioStep = getStep(workflow, "scenarios");
  const procurementStep = getStep(workflow, "procurement");
  const executionStep = getStep(workflow, "execution");
  const mainPayload = engine.dashboard.data || {};
  const capexPayload = engine.capex.data || {};
  const costPayload = engine.costIntelligence.data || {};
  const dataQualityPayload = engine.dataQuality.data || {};
  const costSignals = buildCostSignals(costPayload);
  const dataQualitySignal = buildDataQualitySignal(dataQualityPayload);
  const kpis = { ...(capexPayload.kpis || {}), ...(mainPayload.kpis || {}) };
  const hasPrimaryKpis = Boolean(mainPayload.kpis || capexPayload.kpis);
  const table = mainPayload.table?.length ? mainPayload.table : engine.drilldown.data?.table || [];
  const total = mainPayload.pagination?.total || engine.drilldown.data?.pagination?.total || table.length;
  const barRows = mainPayload.charts?.bar || capexPayload.charts?.bar || [];
  const heatmapRows = engine.heatmap.data?.charts?.heatmap || mainPayload.charts?.heatmap || [];
  const sankeyRows = engine.procurement.data?.charts?.sankey || mainPayload.charts?.sankey || [];
  const timelineRows = engine.timeline.data?.charts?.timeline || mainPayload.charts?.timeline || [];
  const riskRows = engine.risk.data?.charts?.risk_matrix || heatmapRows || table;
  const filterLabel = buildFilterLabel(engine.filters);
  const estimatedSavings = Number(currentSimulation?.kpi?.economie_nette || kpis.economie_nette || 0);
  const procurementGain = Number(kpis.economie_nette || 0);

  const handlePrimaryAction = () => {
    navigateTo(primaryAction.route);
  };

  return (
    <main className="cockpit-page analytics-engine-page">
      <section className="workspace-summary" data-testid="workspace-summary">
        <header className="workspace-summary-hero">
          <div>
            <p className="eyebrow">Synthese projet</p>
            <h1>{project.name || "Projet CAPEX"}</h1>
            <div className={activeDqe ? "workspace-dqe-reference" : "workspace-dqe-reference empty"} aria-label="Fichier DQE de reference">
              {activeDqe ? (
                <>
                  <a href={activeDqeDownloadUrl} download title="Telecharger le fichier DQE actif">📄 {activeDqe.file_name || "Fichier DQE actif"}</a>
                  <span>🔖 Version {activeDqe.version_number ? `V${activeDqe.version_number}` : "-"}</span>
                  <span>📅 {formatDqeDate(activeDqe.uploaded_at || activeDqe.synced_at)}</span>
                  <span>🎯 Trust Score : {activeDqe.trust_score ?? "-"}/100</span>
                </>
              ) : (
                <span>📄 Aucun fichier de référence chargé</span>
              )}
            </div>
            <p>{project.city || "Ville a renseigner"}, {project.country || "Pays a renseigner"} · {project.client_name || "Client a renseigner"}</p>
          </div>
          <div className="workspace-summary-status">
            <span>{workflow.label}</span>
            <strong>Confiance {activeDqe?.trust_score ?? project.trust_score ?? "-"}/100</strong>
            <small>{workflow.completion}% du parcours projet</small>
          </div>
        </header>

        <section className="workspace-next-action">
          <div>
            <span>Prochaine action recommandee</span>
            <strong>{primaryAction.label}</strong>
            <p>{alerts[0]}</p>
          </div>
          <button type="button" className="primary-action" data-testid="workspace-next-action" onClick={handlePrimaryAction}>{primaryAction.label}</button>
        </section>

        <ProjectWorkflowStepper workflow={workflow} onNavigate={navigateTo} onSetup={() => navigateTo("/app/projects")} />

        <SmartWorkflowActions
          workflow={workflow}
          module="dashboard"
          kpis={{ ...kpis, economie_nette: estimatedSavings || procurementGain }}
          simulation={currentSimulation}
          onNavigate={navigateTo}
        />

        <section className="workspace-module-grid">
          <article className={`workspace-module-card ${moduleTone(dqeStep.state)}`}>
            <span>DQE & donnees</span>
            <strong>{dqeStep.status || "A importer"}</strong>
            <p>{activeDqe ? `DQE v${activeDqe.version_number} · ${activeDqe.normalized_lines_count ?? "-"} lignes exploitables` : "Importez un DQE pour analyser le budget du projet."}</p>
            <small>Trust score : {activeDqe?.trust_score ?? "-"}/100</small>
            <button type="button" onClick={() => navigateTo("/app/dqe?tab=import")}>{activeDqe ? "Auditer le DQE projet" : "Importer le DQE budget"}</button>
          </article>

          <article className={`workspace-module-card ${moduleTone(scenarioStep.state)}`}>
            <span>Scenarios</span>
            <strong>{scenarioStep.status || "Bloque"}</strong>
            <p>{currentSimulation ? `${scenario.label} · économie estimée ${formatMoney(estimatedSavings)}` : "Lancez une simulation pour comparer les stratégies CAPEX."}</p>
            <small>Budget : {budgetStep.status || "Bloque"}</small>
            <button type="button" onClick={() => navigateTo("/app/simulation")}>Simuler la stratégie CAPEX</button>
          </article>

          <article className={`workspace-module-card ${moduleTone(procurementStep.state)}`}>
            <span>Approvisionnement</span>
            <strong>{procurementStep.status || "Bloque"}</strong>
            <p>{procurementStep.state === "done" ? "Decisions achat disponibles." : "Preparez les arbitrages achat apres simulation."}</p>
            <small>Gain net securisable : {procurementGain ? formatMoney(procurementGain) : "-"}</small>
            <button type="button" onClick={() => navigateTo("/app/procurement")}>Analyser les arbitrages achat</button>
          </article>

          <article className={`workspace-module-card ${moduleTone(executionStep.state)}`}>
            <span>Préparation Chantier</span>
            <strong>{executionStep.status || "Bloqué"}</strong>
            <p>{executionStep.state === "done" ? "Les lots sont prêts pour coordination chantier." : "En attente des arbitrages achat et logistique."}</p>
            <small>Lots critiques : {executionStep.state === "done" ? "à surveiller" : "-"}</small>
            <button type="button" onClick={() => navigateTo("/app/site?tab=planning")}>Suivre la préparation des lots</button>
          </article>
        </section>

        <section className="workspace-summary-footer">
          <div className="workspace-alerts">
            <span>Alertes projet</span>
            {alerts.map((alert) => <p key={alert}>{alert}</p>)}
          </div>
          <div>
            <span>Actions rapides</span>
            <ProjectQuickActions onNavigate={navigateTo} />
          </div>
        </section>
      </section>

      <section className="page-hero compact">
        <p className="eyebrow">Pilotage consolide</p>
        <h1>Piloter le budget, les risques et les arbitrages du projet</h1>
        <p>L'analyse SP2I consolide les indicateurs, les filtres et les decisions local/import sur les donnees du projet.</p>
      </section>

      {engine.error ? <div className="app-error">{engine.error.message}</div> : null}

      <GlobalAnalyticsFilters />
      {engine.isFetching ? <div className="live-refresh">Synchronisation du cockpit en cours...</div> : null}

      {engine.error && !hasPrimaryKpis ? null : <EnterpriseKpiGrid kpis={kpis} loading={engine.isLoading} />}
      {costSignals.length || dataQualityPayload.kpis ? (
        <section className="cost-intelligence-strip" aria-label="Cost Intelligence">
          <article className="cost-intelligence-card data-quality">
            <span>{dataQualitySignal.label}</span>
            <strong>{dataQualitySignal.value}</strong>
            <small>{dataQualitySignal.detail}</small>
          </article>
          {costSignals.map((signal) => (
            <article className="cost-intelligence-card" key={signal.label}>
              <span>{signal.label}</span>
              <strong>{signal.value}</strong>
              <small>{signal.detail}</small>
            </article>
          ))}
        </section>
      ) : null}
      {engine.isLoading ? <Skeleton /> : null}

      <section className="analytics-command-grid">
        <InsightsPanel kpis={kpis} barRows={barRows} table={table} />
        <AnalyticsCard title="Du budget initial au budget optimise" eyebrow="Vue direction">
          <CapexWaterfall summary={kpis} filtersLabel={filterLabel} />
        </AnalyticsCard>
      </section>

      <section className="bi-dashboard-grid">
        <AnalyticsCard title="Repartition des achats local / import" eyebrow="Arbitrage achats">
          <ImportDecisionSankey rows={table} chartRows={barRows} sankeyRows={sankeyRows} filtersLabel={filterLabel} />
        </AnalyticsCard>
        <AnalyticsCard title="Zones les plus couteuses" eyebrow="Lots et familles">
          <CapexHeatmap data={heatmapRows} rows={table} filtersLabel={filterLabel} />
        </AnalyticsCard>
        <AnalyticsCard title="Carte des risques projet" eyebrow="Pilotage projet">
          <RiskMatrix rows={riskRows} filtersLabel={filterLabel} />
        </AnalyticsCard>
        <AnalyticsCard title="Evolution financiere du projet" eyebrow="Strategies et economies">
          <CapexTimeline data={timelineRows} filtersLabel={filterLabel} />
        </AnalyticsCard>
      </section>

      <AnalyticsCard title="Analyse detaillee des lignes budgetaires" eyebrow={`${Number(total || table.length).toLocaleString("fr-FR")} lignes chargees`}>
        <FactMetreGrid rows={table} total={total} filtersLabel={filterLabel} />
      </AnalyticsCard>
    </main>
  );
}
