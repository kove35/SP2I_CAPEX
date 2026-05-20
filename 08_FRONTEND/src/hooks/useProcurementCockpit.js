import { useQuery } from "@tanstack/react-query";
import { getProcurementCockpit } from "../services/procurementCockpitService";
import { buildAnalyticsQueryKey } from "../services/analyticsQueryBuilder";
import { useCrossFiltering } from "./useCrossFiltering";

export function useProcurementCockpit() {
  const crossFiltering = useCrossFiltering();
  const query = useQuery({
    queryKey: buildAnalyticsQueryKey("procurement-enterprise-cockpit", crossFiltering.filters),
    queryFn: () => getProcurementCockpit(crossFiltering.filters),
    staleTime: 45_000,
    placeholderData: (previousData) => previousData,
  });

  return {
    ...query,
    crossFiltering,
    filters: crossFiltering.filters,
    activeChips: crossFiltering.activeChips,
  };
}
