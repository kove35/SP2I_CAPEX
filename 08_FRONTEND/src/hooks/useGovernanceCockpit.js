import { useQuery } from "@tanstack/react-query";
import { getGovernanceCockpit } from "../services/governanceCockpitService";
import { useGovernanceCockpitStore } from "../stores/governanceCockpitStore";

export function useGovernanceCockpit() {
  const filters = useGovernanceCockpitStore((state) => state.filters);
  const selectedReferenceId = useGovernanceCockpitStore((state) => state.selectedReferenceId);
  const query = useQuery({
    queryKey: ["governance-cockpit", filters],
    queryFn: getGovernanceCockpit,
    staleTime: 60_000,
    placeholderData: (previousData) => previousData,
  });

  const references = query.data?.references || [];
  const filteredReferences = references.filter((row) => {
    if (filters.family && row.family !== filters.family) return false;
    if (filters.priority && row.reviewPriority !== filters.priority) return false;
    if (filters.escalation && row.escalationLevel !== filters.escalation) return false;
    if (filters.status && row.reviewStatus !== filters.status) return false;
    return true;
  });
  const selectedReference = references.find((row) => row.referenceId === selectedReferenceId) || filteredReferences[0] || null;

  return {
    ...query,
    data: query.data,
    references: filteredReferences,
    selectedReference,
    filters,
  };
}
