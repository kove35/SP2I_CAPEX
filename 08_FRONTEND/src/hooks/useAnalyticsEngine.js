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
import { useDashboardStore } from "../store/dashboardStore";

export function useAnalyticsEngine(dashboardType = "direction") {
  const filters = useDashboardStore((state) => state.filters);

  const dashboard = useQuery({
    queryKey: ["analytics-dashboard", dashboardType, filters],
    queryFn: () => getAnalyticsDashboard(filters, dashboardType),
    staleTime: 20_000,
  });

  const capex = useQuery({
    queryKey: ["analytics-capex", filters],
    queryFn: () => getAnalyticsCapex(filters),
    staleTime: 20_000,
  });

  const procurement = useQuery({
    queryKey: ["analytics-procurement", filters],
    queryFn: () => getAnalyticsProcurement(filters),
    staleTime: 20_000,
  });

  const heatmap = useQuery({
    queryKey: ["analytics-heatmap", filters],
    queryFn: () => getAnalyticsHeatmap(filters),
    staleTime: 20_000,
  });

  const risk = useQuery({
    queryKey: ["analytics-risk", filters],
    queryFn: () => getAnalyticsRisk(filters),
    staleTime: 20_000,
  });

  const timeline = useQuery({
    queryKey: ["analytics-timeline", filters],
    queryFn: () => getAnalyticsTimeline(filters),
    staleTime: 20_000,
  });

  const drilldown = useQuery({
    queryKey: ["analytics-drilldown", filters],
    queryFn: () => getAnalyticsDrilldown(filters),
    staleTime: 20_000,
  });

  const qa = useQuery({
    queryKey: ["analytics-qa-summary"],
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
