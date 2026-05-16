import { useQuery } from "@tanstack/react-query";
import { getCapexSummary, getFactMetre, getMonitoringStatus, getScenarioHistory } from "../services/dashboardService";
import { useDashboardStore } from "../store/dashboardStore";

export function useDashboardData() {
  const filters = useDashboardStore((state) => state.filters);

  const summary = useQuery({
    queryKey: ["capex-summary"],
    queryFn: getCapexSummary,
  });

  const factMetre = useQuery({
    queryKey: ["fact-metre", filters],
    queryFn: () => getFactMetre(filters, 1000),
  });

  const monitoring = useQuery({
    queryKey: ["monitoring-status"],
    queryFn: getMonitoringStatus,
  });

  const scenarios = useQuery({
    queryKey: ["scenario-history"],
    queryFn: getScenarioHistory,
  });

  return {
    filters,
    summary,
    factMetre,
    monitoring,
    scenarios,
    isLoading: summary.isLoading || factMetre.isLoading,
    isError: summary.isError || factMetre.isError,
  };
}
