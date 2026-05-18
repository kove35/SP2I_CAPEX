import { useQuery } from "@tanstack/react-query";
import {
  getAnalyticsCapex,
  getAnalyticsDashboard,
  getAnalyticsDrilldown,
  getAnalyticsHeatmap,
  getAnalyticsProcurement,
  getAnalyticsQaSummary,
  getAnalyticsRisk,
  getAnalyticsTimeline,
} from "../services/analyticsService";
import { buildAnalyticsQueryKey } from "../services/analyticsQueryBuilder";
import { useAnalyticsFilters } from "./useAnalyticsFilters";

export function useAnalyticsEngine(dashboardType = "direction") {
  const { filters, debouncedFilters } = useAnalyticsFilters();

  const dashboard = useQuery({
    queryKey: buildAnalyticsQueryKey("dashboard", debouncedFilters, { dashboardType }),
    queryFn: () => getAnalyticsDashboard(debouncedFilters, dashboardType),
    staleTime: 20_000,
  });

  const capex = useQuery({
    queryKey: buildAnalyticsQueryKey("capex", debouncedFilters),
    queryFn: () => getAnalyticsCapex(debouncedFilters),
    staleTime: 20_000,
  });

  const procurement = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement", debouncedFilters),
    queryFn: () => getAnalyticsProcurement(debouncedFilters),
    staleTime: 20_000,
  });

  const heatmap = useQuery({
    queryKey: buildAnalyticsQueryKey("heatmap", debouncedFilters),
    queryFn: () => getAnalyticsHeatmap(debouncedFilters),
    staleTime: 20_000,
  });

  const risk = useQuery({
    queryKey: buildAnalyticsQueryKey("risk", debouncedFilters),
    queryFn: () => getAnalyticsRisk(debouncedFilters),
    staleTime: 20_000,
  });

  const timeline = useQuery({
    queryKey: buildAnalyticsQueryKey("timeline", debouncedFilters),
    queryFn: () => getAnalyticsTimeline(debouncedFilters),
    staleTime: 20_000,
  });

  const drilldown = useQuery({
    queryKey: buildAnalyticsQueryKey("drilldown", debouncedFilters),
    queryFn: () => getAnalyticsDrilldown(debouncedFilters),
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
    heatmap,
    risk,
    timeline,
    drilldown,
    qa,
    isLoading: dashboard.isLoading || capex.isLoading,
    isFetching: dashboard.isFetching || capex.isFetching || drilldown.isFetching,
    error: dashboard.error || capex.error || procurement.error || heatmap.error || risk.error || timeline.error || drilldown.error,
  };
}
