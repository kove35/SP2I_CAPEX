import { useQuery } from "@tanstack/react-query";
import { useAppStore } from "../../../store/appStore.jsx";
import { useCrossFiltering } from "../../../hooks/useCrossFiltering";
import {
  getAnalyticsDashboard,
  getAnalyticsImportRisks,
  getAnalyticsProcurement,
  getAnalyticsProcurementLines,
  getAnalyticsRisk,
  getAnalyticsTimeline,
} from "../../../services/analyticsService";
import { buildAnalyticsQueryKey } from "../../../services/analyticsQueryBuilder";
import { listProjectExecutionActions, listProjectProcurementDecisions } from "../../../services/projectService";
import { useWorkflow } from "../../../hooks/useWorkflow";
import { buildApprovisionnementDashboard } from "../services/approvisionnementAdapter";

async function settle(value) {
  try {
    return await value;
  } catch {
    return null;
  }
}

export function useApprovisionnementDashboard() {
  const { state } = useAppStore();
  const crossFiltering = useCrossFiltering();
  const project = state.activeProjectDetails || { id: state.activeProject, workspace_key: state.activeProject };
  const { workflow } = useWorkflow(project?.id || state.activeProject, project);
  const projectId = project?.id || state.activeProject;
  const scenarioId = workflow.scenario?.scenario_id || state.activeScenario;

  const query = useQuery({
    queryKey: buildAnalyticsQueryKey("approvisionnement-dashboard", crossFiltering.filters, {
      projectId,
      scenarioId,
      workflowStatus: workflow.status,
    }),
    queryFn: async () => {
      const [
        dashboard,
        procurement,
        procurementLines,
        importRisks,
        risk,
        timeline,
        decisions,
        executionActions,
      ] = await Promise.all([
        settle(getAnalyticsDashboard(crossFiltering.filters, "procurement")),
        settle(getAnalyticsProcurement(crossFiltering.filters)),
        settle(getAnalyticsProcurementLines(crossFiltering.filters)),
        settle(getAnalyticsImportRisks(crossFiltering.filters)),
        settle(getAnalyticsRisk(crossFiltering.filters)),
        settle(getAnalyticsTimeline(crossFiltering.filters)),
        settle(listProjectProcurementDecisions(projectId, scenarioId)),
        settle(listProjectExecutionActions(projectId, scenarioId)),
      ]);

      return buildApprovisionnementDashboard({
        dashboard,
        procurement,
        procurementLines,
        importRisks,
        risk,
        timeline,
        decisions,
        executionActions,
        workflow,
      });
    },
    staleTime: 45_000,
    placeholderData: (previousData) => previousData,
  });

  return {
    ...query,
    project,
    workflow,
    filters: crossFiltering.filters,
    activeChips: crossFiltering.activeChips,
    crossFiltering,
  };
}
