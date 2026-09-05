import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getAnalyticsCapex,
  getAnalyticsCostIntelligence,
  getAnalyticsCostIntelligenceV6,

  getAnalyticsDashboard,
  getAnalyticsDashboardV6,
  getAnalyticsDrilldown,
  getAnalyticsGainAnalysis,
  getAnalyticsHeatmap,
  getAnalyticsCurrency,
  getAnalyticsDataQuality,
  getAnalyticsImportRisks,
  getAnalyticsProcurement,
  getAnalyticsProcurementLines,
  getAnalyticsProcurementScenarios,
  getAnalyticsQaSummary,
  getAnalyticsRisk,
  getAnalyticsSuppliers,
  getAnalyticsTimeline,
} from "../services/analyticsService";
import { buildAnalyticsQueryKey } from "../services/analyticsQueryBuilder";
import { useAnalyticsFilters } from "./useAnalyticsFilters";
import { useAppStore } from "../store/appStore.jsx";
import { useAnalyticsFilterStore } from "../stores/analyticsFilterStore";
import { getProjectWorkspaceKey } from "../services/projectService";
import { markPerformance, measurePerformance } from "../services/performanceMonitor";


const logAnalyticsResult = (label, data, filters) => {
  console.log("Analytics query result", label, {
    filters,
    nb_lignes: data?.kpis?.nb_lignes,
    pagination_total: data?.pagination?.total,
    tableLength: data?.table?.length,
    kpis: data?.kpis,
  });
  try {
    if (typeof window !== "undefined") {
      window.__REACT_QUERY_CACHE = window.__REACT_QUERY_CACHE || {};
      window.__REACT_QUERY_CACHE[label] = data;
    }
  } catch (e) {
    // ignore
  }
};

const analyticsRetry = {
  retry: 1,
  retryDelay: 1000,
  gcTime: 5 * 60_000,
};

const ANALYTICS_QUERY_PLAN = [
  { endpoint: "/analytics/dashboard", query: "dashboard", priority: 1, trigger: "montage AnalyticsPage", enabled: "immediat" },
  { endpoint: "/analytics/capex", query: "capex", priority: 1, trigger: "montage AnalyticsPage", enabled: "immediat" },
  { endpoint: "/analytics/filters", query: "filters", priority: 1, trigger: "GlobalAnalyticsFilters", enabled: "immediat hors useAnalyticsEngine" },
  { endpoint: "/analytics/risk", query: "risk", priority: 2, trigger: "dashboard + capex prets", enabled: "primaryReady" },
  { endpoint: "/analytics/drilldown", query: "drilldown", priority: 2, trigger: "dashboard + capex prets", enabled: "primaryReady" },
  { endpoint: "/analytics/heatmap", query: "heatmap", priority: 2, trigger: "dashboard + capex prets", enabled: "primaryReady" },
  { endpoint: "/analytics/timeline", query: "timeline", priority: 2, trigger: "dashboard + capex prets", enabled: "primaryReady" },
  { endpoint: "/analytics/procurement", query: "procurement", priority: 3, trigger: "niveau 2 termine", enabled: "secondaryReady" },
  { endpoint: "/analytics/suppliers", query: "suppliers", priority: 3, trigger: "niveau 2 termine", enabled: "secondaryReady" },
  { endpoint: "/analytics/qa-summary", query: "qa-summary", priority: 3, trigger: "niveau 2 termine", enabled: "secondaryReady" },
  { endpoint: "/analytics/gain-analysis", query: "gain-analysis", priority: 3, trigger: "niveau 2 termine", enabled: "secondaryReady" },
  { endpoint: "/analytics/cost-intelligence", query: "cost-intelligence", priority: 3, trigger: "niveau 2 termine", enabled: "secondaryReady" },
  { endpoint: "/analytics/data-quality", query: "data-quality", priority: 3, trigger: "niveau 2 termine", enabled: "secondaryReady" },
  { endpoint: "/analytics/procurement-lines", query: "procurement-lines", priority: 4, trigger: "vue procurement", enabled: "deferredProcurementReady" },
  { endpoint: "/analytics/procurement-scenarios", query: "procurement-scenarios", priority: 4, trigger: "vue procurement", enabled: "deferredProcurementReady" },
  { endpoint: "/analytics/currency", query: "currency", priority: 4, trigger: "vue procurement/logistics", enabled: "deferredTradeReady" },
  { endpoint: "/analytics/import-risks", query: "import-risks", priority: 4, trigger: "vue procurement/logistics", enabled: "deferredTradeReady" },
];

export const V6_FINANCIALS_ENABLED = String(import.meta.env.VITE_SP2I_USE_V6_FINANCIALS || "").toLowerCase() === "true";
const USE_V6_FINANCIALS = V6_FINANCIALS_ENABLED;

function querySettled(query) {
  return query.isSuccess || query.isError;
}

function hasDashboardSuccess(query) {
  return Boolean(query.data?.kpis || query.data?.status === "SUCCESS" || query.isSuccess);
}

export function useAnalyticsEngine(dashboardType = "direction") {
  const { filters, debouncedFilters } = useAnalyticsFilters();
  const { state: appState } = useAppStore();
  const setAnalyticsFilter = useAnalyticsFilterStore((store) => store.setFilter);
  const replaceAnalyticsFilters = useAnalyticsFilterStore((store) => store.replaceFilters);
  const useV6Financials = USE_V6_FINANCIALS && dashboardType === "direction";
  const shouldLoadProcurementScenarios = dashboardType === "procurement";
  const shouldLoadProcurementDetails = dashboardType === "procurement";
  const shouldLoadTradeDetails = dashboardType === "procurement" || dashboardType === "logistics";

  // Anomalie A — Isolation des contextes : le projet actif (appStore) doit piloter le
  // filtre `projet` du store analytics. Quand le projet change, on réinitialise les
  // filtres spatiaux pour éviter de mélanger les données de deux projets.
  const activeProjectKey = React.useMemo(() => {
    const details = appState.activeProjectDetails;
    if (details) return getProjectWorkspaceKey(details) || details.workspace_key || details.code || appState.activeProject;
    return appState.activeProject;
  }, [appState.activeProject, appState.activeProjectDetails]);

  const lastSyncedProject = React.useRef(null);
  React.useEffect(() => {
    if (!activeProjectKey) return;
    if (lastSyncedProject.current === activeProjectKey) return;
    lastSyncedProject.current = activeProjectKey;
    const currentProject = filters.projet;
    if (currentProject && currentProject !== activeProjectKey) {
      // Changement de projet : on resynchronise le filtre projet et on purge les filtres spatiaux.
      replaceAnalyticsFilters({
        projet: activeProjectKey,
        scenario: filters.scenario,
        devise: filters.devise,
        batiment: "",
        niveau: "",
        appartement: "",
        piece: "",
        lot: "",
        famille: "",
        fournisseur: "",
        importLocal: "",
        decisionImport: "",
        dateDebut: "",
        dateFin: "",
        periodeDebut: "",
        periodeFin: "",
      });
    } else if (!currentProject) {
      setAnalyticsFilter("projet", activeProjectKey);
    }
  }, [activeProjectKey, filters.projet, filters.scenario, filters.devise, replaceAnalyticsFilters, setAnalyticsFilter]);

  console.log("Analytics filters", debouncedFilters);
  console.table(ANALYTICS_QUERY_PLAN);


  const dashboard = useQuery({
    queryKey: buildAnalyticsQueryKey("dashboard", debouncedFilters, { dashboardType, financialMode: useV6Financials ? "v6" : "v5" }),
    queryFn: () => {
      markPerformance("dashboard_request");
      console.log("Query refresh", "analytics-dashboard", debouncedFilters);
      return useV6Financials ? getAnalyticsDashboardV6(debouncedFilters) : getAnalyticsDashboard(debouncedFilters, dashboardType);
    },
    onSuccess: (data) => {
      markPerformance("dashboard_response");
      const elapsed = measurePerformance("dashboard_api_ms", "dashboard_request", "dashboard_response");
      console.log("ANALYTICS PERFORMANCE", { dashboard_api_ms: elapsed });
      logAnalyticsResult("dashboard", data, debouncedFilters);
    },
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const dashboardSuccess = hasDashboardSuccess(dashboard);
  const dashboardReady = dashboardSuccess;

  const capex = useQuery({
    queryKey: buildAnalyticsQueryKey("capex", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-capex", debouncedFilters);
      return getAnalyticsCapex(debouncedFilters);
    },
    onSuccess: (data) => logAnalyticsResult("capex", data, debouncedFilters),
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const capexReady = Boolean(capex.data?.kpis) || capex.isSuccess;
  const primaryReady = dashboardReady && capexReady;

  const heatmap = useQuery({
    queryKey: buildAnalyticsQueryKey("heatmap", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-heatmap", debouncedFilters);
      return getAnalyticsHeatmap(debouncedFilters);
    },
    enabled: primaryReady,
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const risk = useQuery({
    queryKey: buildAnalyticsQueryKey("risk", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-risk", debouncedFilters);
      return getAnalyticsRisk(debouncedFilters);
    },
    enabled: primaryReady,
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const timeline = useQuery({
    queryKey: buildAnalyticsQueryKey("timeline", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-timeline", debouncedFilters);
      return getAnalyticsTimeline(debouncedFilters);
    },
    enabled: primaryReady,
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const drilldown = useQuery({
    queryKey: buildAnalyticsQueryKey("drilldown", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-drilldown", debouncedFilters);
      return getAnalyticsDrilldown(debouncedFilters);
    },
    enabled: primaryReady,
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const secondaryReady = [heatmap, risk, timeline, drilldown].every(querySettled);

  const procurement = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-procurement", debouncedFilters);
      return getAnalyticsProcurement(debouncedFilters);
    },
    enabled: secondaryReady,
    onSuccess: (data) => logAnalyticsResult("procurement", data, debouncedFilters),
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const gainAnalysis = useQuery({
    queryKey: buildAnalyticsQueryKey("gain-analysis", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-gain-analysis", debouncedFilters);
      return getAnalyticsGainAnalysis(debouncedFilters);
    },
    enabled: secondaryReady,
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const suppliers = useQuery({
    queryKey: buildAnalyticsQueryKey("suppliers", debouncedFilters),
    queryFn: () => getAnalyticsSuppliers(debouncedFilters),
    enabled: secondaryReady,
    staleTime: 60_000,
    ...analyticsRetry,
  });

  const qa = useQuery({
    queryKey: buildAnalyticsQueryKey("qa-summary", debouncedFilters),
    queryFn: getAnalyticsQaSummary,
    enabled: secondaryReady,
    staleTime: 30_000,
    ...analyticsRetry,
  });

  const costIntelligence = useQuery({
    queryKey: buildAnalyticsQueryKey("cost-intelligence", debouncedFilters, { financialMode: useV6Financials ? "v6" : "v5" }),
    queryFn: () => {
      console.log("Query refresh", "analytics-cost-intelligence", debouncedFilters);
      return useV6Financials ? getAnalyticsCostIntelligenceV6(debouncedFilters) : getAnalyticsCostIntelligence(debouncedFilters);
    },
    enabled: secondaryReady,
    onSuccess: (data) => logAnalyticsResult("cost-intelligence", data, debouncedFilters),
    staleTime: 30_000,
    ...analyticsRetry,
  });

  const dataQuality = useQuery({
    queryKey: buildAnalyticsQueryKey("data-quality", debouncedFilters),
    queryFn: getAnalyticsDataQuality,
    enabled: secondaryReady,
    onSuccess: (data) => logAnalyticsResult("data-quality", data, debouncedFilters),
    staleTime: 60_000,
    ...analyticsRetry,
  });

  const tertiaryReady = [procurement, gainAnalysis, suppliers, qa, costIntelligence, dataQuality].every(querySettled);
  const deferredProcurementReady = tertiaryReady && shouldLoadProcurementDetails;
  const deferredTradeReady = tertiaryReady && shouldLoadTradeDetails;

  const procurementScenarios = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement-scenarios", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-procurement-scenarios", debouncedFilters);
      return getAnalyticsProcurementScenarios(debouncedFilters).catch((error) => {
        console.error("Analytics secondary query error", {
          endpoint: "/analytics/procurement-scenarios",
          message: error?.message,
          filters: debouncedFilters,
        });
        throw error;
      });
    },
    enabled: deferredProcurementReady && shouldLoadProcurementScenarios,
    onSuccess: (data) => logAnalyticsResult("procurement-scenarios", data, debouncedFilters),
    staleTime: 30_000,
    ...analyticsRetry,
  });

  const procurementLines = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement-lines", debouncedFilters),
    queryFn: () => getAnalyticsProcurementLines(debouncedFilters),
    enabled: deferredProcurementReady,
    onSuccess: (data) => logAnalyticsResult("procurement-lines", data, debouncedFilters),
    staleTime: 20_000,
    ...analyticsRetry,
  });

  const currency = useQuery({
    queryKey: buildAnalyticsQueryKey("currency", debouncedFilters),
    queryFn: () => getAnalyticsCurrency(debouncedFilters),
    enabled: deferredTradeReady,
    staleTime: 120_000,
    ...analyticsRetry,
  });

  const importRisks = useQuery({
    queryKey: buildAnalyticsQueryKey("import-risks", debouncedFilters),
    queryFn: () => getAnalyticsImportRisks(debouncedFilters),
    enabled: deferredTradeReady,
    staleTime: 30_000,
    ...analyticsRetry,
  });

  const criticalError = dashboard.isError && !dashboardSuccess ? dashboard.error : null;
  const secondaryErrors = [
    capex.error,
    procurement.error,
    gainAnalysis.error,
    suppliers.error,
    procurementLines.error,
    procurementScenarios.error,
    currency.error,
    importRisks.error,
    costIntelligence.error,
    dataQuality.error,
    heatmap.error,
    risk.error,
    timeline.error,
    drilldown.error,
  ].filter(Boolean);

  if (secondaryErrors.length) {
    console.warn("Analytics secondary queries degraded", secondaryErrors.map((error) => error.message));
  }

  console.log("dashboard success", {
    status: dashboard.status,
    isSuccess: dashboard.isSuccess,
    isError: dashboard.isError,
    hasKpis: Boolean(dashboard.data?.kpis),
    error: dashboard.error?.message,
  });
  console.log("dashboard error", {
    status: dashboard.status,
    isSuccess: dashboard.isSuccess,
    isError: dashboard.isError,
    hasKpis: Boolean(dashboard.data?.kpis),
    error: dashboard.error?.message,
    ignored_because_success: Boolean(dashboard.error && dashboardSuccess),
  });
  console.log("engine.error", {
    message: criticalError?.message || null,
    dashboardQuery: {
      status: dashboard.status,
      isSuccess: dashboard.isSuccess,
      isError: dashboard.isError,
    },
  });

  console.log("Analytics engine state", {
    dashboardType,
    dashboard: { status: dashboard.status, isFetching: dashboard.isFetching, isSuccess: dashboard.isSuccess, isError: dashboard.isError, hasKpis: Boolean(dashboard.data?.kpis), error: dashboard.error?.message },
    capex: { status: capex.status, isFetching: capex.isFetching, hasKpis: Boolean(capex.data?.kpis), error: capex.error?.message },
    gates: {
      dashboardReady,
      capexReady,
      primaryReady,
      secondaryReady,
      tertiaryReady,
      deferredProcurementReady,
      deferredTradeReady,
    },
    criticalError: criticalError?.message,
  });

  return {
    filters,
    dashboard,
    capex,
    procurement,
    gainAnalysis,
    suppliers,
    procurementLines,
    procurementScenarios,
    currency,
    importRisks,
    costIntelligence,
    dataQuality,
    heatmap,
    risk,
    timeline,
    drilldown,
    qa,
    isLoading: dashboard.isLoading && !dashboard.data?.kpis,
    isFetching: dashboard.isFetching,
    backgroundFetching: capex.isFetching || procurement.isFetching || gainAnalysis.isFetching || costIntelligence.isFetching || dataQuality.isFetching || suppliers.isFetching || procurementLines.isFetching || procurementScenarios.isFetching || currency.isFetching || importRisks.isFetching || heatmap.isFetching || risk.isFetching || timeline.isFetching || drilldown.isFetching,
    error: criticalError,
    secondaryErrors,
  };
}

// Debug helper: log cached values for key queries
if (typeof window !== "undefined") {
  setTimeout(() => {
    try {
      console.log("REACT-QUERY CACHE SNAPSHOT: dashboard", { data: window.__REACT_QUERY_DASHBOARD_DATA });
    } catch (e) {
      // noop
    }
  }, 1000);
}
