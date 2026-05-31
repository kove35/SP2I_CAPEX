import { useQuery } from "@tanstack/react-query";
import {
  getAnalyticsCapex,
  getAnalyticsDashboard,
  getAnalyticsDrilldown,
  getAnalyticsGainAnalysis,
  getAnalyticsHeatmap,
  getAnalyticsCurrency,
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

export function useAnalyticsEngine(dashboardType = "direction") {
  const { filters, debouncedFilters } = useAnalyticsFilters();

  console.log("Analytics filters", debouncedFilters);

  const dashboard = useQuery({
    queryKey: buildAnalyticsQueryKey("dashboard", debouncedFilters, { dashboardType }),
    queryFn: () => {
      console.log("Query refresh", "analytics-dashboard", debouncedFilters);
      return getAnalyticsDashboard(debouncedFilters, dashboardType);
    },
    onSuccess: (data) => logAnalyticsResult("dashboard", data, debouncedFilters),
    staleTime: 20_000,
  });

  const capex = useQuery({
    queryKey: buildAnalyticsQueryKey("capex", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-capex", debouncedFilters);
      return getAnalyticsCapex(debouncedFilters);
    },
    onSuccess: (data) => logAnalyticsResult("capex", data, debouncedFilters),
    staleTime: 20_000,
  });

  const procurement = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-procurement", debouncedFilters);
      return getAnalyticsProcurement(debouncedFilters);
    },
    onSuccess: (data) => logAnalyticsResult("procurement", data, debouncedFilters),
    staleTime: 20_000,
  });

  const gainAnalysis = useQuery({
    queryKey: buildAnalyticsQueryKey("gain-analysis", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-gain-analysis", debouncedFilters);
      return getAnalyticsGainAnalysis(debouncedFilters);
    },
    staleTime: 20_000,
  });

  const suppliers = useQuery({
    queryKey: buildAnalyticsQueryKey("suppliers", debouncedFilters),
    queryFn: () => getAnalyticsSuppliers(debouncedFilters),
    staleTime: 60_000,
  });

  const procurementScenarios = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement-scenarios", debouncedFilters),
    queryFn: () => getAnalyticsProcurementScenarios(debouncedFilters),
    staleTime: 30_000,
  });

  const procurementLines = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement-lines", debouncedFilters),
    queryFn: () => getAnalyticsProcurementLines(debouncedFilters),
    onSuccess: (data) => logAnalyticsResult("procurement-lines", data, debouncedFilters),
    staleTime: 20_000,
  });

  const currency = useQuery({
    queryKey: buildAnalyticsQueryKey("currency", debouncedFilters),
    queryFn: () => getAnalyticsCurrency(debouncedFilters),
    staleTime: 120_000,
  });

  const importRisks = useQuery({
    queryKey: buildAnalyticsQueryKey("import-risks", debouncedFilters),
    queryFn: () => getAnalyticsImportRisks(debouncedFilters),
    staleTime: 30_000,
  });

  const heatmap = useQuery({
    queryKey: buildAnalyticsQueryKey("heatmap", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-heatmap", debouncedFilters);
      return getAnalyticsHeatmap(debouncedFilters);
    },
    staleTime: 20_000,
  });

  const risk = useQuery({
    queryKey: buildAnalyticsQueryKey("risk", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-risk", debouncedFilters);
      return getAnalyticsRisk(debouncedFilters);
    },
    staleTime: 20_000,
  });

  const timeline = useQuery({
    queryKey: buildAnalyticsQueryKey("timeline", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-timeline", debouncedFilters);
      return getAnalyticsTimeline(debouncedFilters);
    },
    staleTime: 20_000,
  });

  const drilldown = useQuery({
    queryKey: buildAnalyticsQueryKey("drilldown", debouncedFilters),
    queryFn: () => {
      console.log("Query refresh", "analytics-drilldown", debouncedFilters);
      return getAnalyticsDrilldown(debouncedFilters);
    },
    staleTime: 20_000,
  });

  const qa = useQuery({
    queryKey: buildAnalyticsQueryKey("qa-summary", debouncedFilters),
    queryFn: getAnalyticsQaSummary,
    staleTime: 30_000,
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
    heatmap,
    risk,
    timeline,
    drilldown,
    qa,
    isLoading: dashboard.isLoading || capex.isLoading,
    isFetching: dashboard.isFetching || capex.isFetching || drilldown.isFetching || gainAnalysis.isFetching,
    error: dashboard.error || capex.error || procurement.error || gainAnalysis.error || suppliers.error || procurementLines.error || procurementScenarios.error || currency.error || importRisks.error || heatmap.error || risk.error || timeline.error || drilldown.error,
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
