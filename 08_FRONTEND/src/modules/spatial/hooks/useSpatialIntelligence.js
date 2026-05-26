import { useQuery } from "@tanstack/react-query";
import { useAppStore } from "../../../store/appStore.jsx";
import { getProjectSpatialSummary, getProjectWorkflow, listProjectExecutionActions } from "../../../services/projectService";
import { useSpatialFilterStore } from "../store/spatialFilterStore";

async function settle(promise) {
  try {
    return await promise;
  } catch {
    return null;
  }
}

function fallbackSpatialSummary(workflow, actions = []) {
  const maturity = workflow?.dqe?.bim_maturity || workflow?.activeDqe?.bim_maturity || {
    maturity: "NON_BIM",
    mode: "NON_BIM",
    is_bim_compatible: false,
  };
  const isSpatial = (maturity.mode || maturity.maturity) !== "NON_BIM";
  const zone = "Bâtiment principal";
  const defaultHierarchy = isSpatial
    ? [
        {
          id: "batiment-principal",
          level: "batiment",
          label: zone,
          capex_local: 0,
          lines_count: Number(maturity.spatialized_lines_count || 0),
          risk_count: 0,
          children: [],
        },
      ]
    : [];

  return {
    project_id: null,
    maturity,
    kpis: {
      spatialized_lines_count: Number(maturity.spatialized_lines_count || 0),
      batiments_count: Number(maturity.coverage?.batiment ? 1 : 0),
      niveaux_count: Number(maturity.coverage?.niveau ? 1 : 0),
      pieces_count: Number(maturity.coverage?.piece ? 1 : 0),
      capex_spatialized: 0,
      execution_actions_spatialized: actions.filter((action) => action.batiment || action.niveau || action.piece).length,
      spatial_risks_count: actions.filter((action) => ["AT_RISK", "BLOCKED"].includes(action.status)).length,
    },
    hierarchy: defaultHierarchy,
    capex_by_batiment: isSpatial ? [{ level: "batiment", label: zone, capex_local: 0, lines_count: Number(maturity.spatialized_lines_count || 0), risk_count: 0 }] : [],
    capex_by_niveau: [],
    capex_by_piece: [],
    execution_by_space: isSpatial ? [{ batiment: zone, niveau: "", piece: "", actions_count: actions.length || 1, open_count: 1, done_count: 0, at_risk_count: 0, blocked_count: 0 }] : [],
    risk_heatmap: [],
    timeline: isSpatial
      ? [
          {
            zone,
            batiment: zone,
            niveau: "",
            piece: "",
            lot: "Coordination",
            action_type: "PLANNING",
            status: "TO_DO",
            risk_level: "MEDIUM",
            delivery_date: new Date().toISOString(),
            installation_date: new Date(Date.now() + 2 * 86_400_000).toISOString(),
            validation_date: new Date(Date.now() + 4 * 86_400_000).toISOString(),
            is_critical: false,
            message: "Action chantier à planifier.",
          },
        ]
      : [],
    dependencies: isSpatial
      ? {
          nodes: [
            { id: `${zone}:PLANNING`, zone, label: "PLANNING", status: "TO_DO", risk_level: "MEDIUM" },
            { id: `${zone}:COORDINATION`, zone, label: "COORDINATION", status: "TO_DO", risk_level: "MEDIUM" },
          ],
          edges: [{ source: `${zone}:PLANNING`, target: `${zone}:COORDINATION`, relation: "spatial_sequence" }],
        }
      : { nodes: [], edges: [] },
    event_feed: isSpatial
      ? [
          {
            event_type: "SPATIAL_PLANNING",
            severity: "info",
            zone,
            message: "Timeline spatiale initialisée en mode fallback local.",
            recommended_action: "Préparer les actions chantier par zone.",
          },
        ]
      : [],
    planning: isSpatial
      ? {
          critical_path_count: 0,
          dependency_edges_count: 1,
          recommendations: ["Planning spatial initialisé. Compléter les actions chantier pour calculer les chemins critiques."],
        }
      : {},
    storage: isSpatial ? [{ zone, storage_impact: 0, actions_count: actions.length || 1, risk_count: 0, saturation_level: "LOW", message: "Stockage sans alerte majeure." }] : [],
    risk_propagation: isSpatial
      ? [{ source_event: "SPATIAL_PLANNING", zone, severity: "info", chain: ["Approvisionnement", "Pose", "Validation", "Réception"], message: "Dépendances spatiales prêtes pour orchestration." }]
      : [],
  };
}

export function useSpatialIntelligence({ workflow: providedWorkflow } = {}) {
  const { state } = useAppStore();
  const project = state.activeProjectDetails || { id: state.activeProject, workspace_key: state.activeProject };
  const workflow = providedWorkflow || getProjectWorkflow(project, state);
  const projectId = project?.id || state.activeProject;
  const scenarioId = workflow?.scenario?.scenario_id || state.activeScenario;
  const filters = useSpatialFilterStore((store) => store.filters);
  const setSpatialFilter = useSpatialFilterStore((store) => store.setSpatialFilter);
  const resetSpatialFilters = useSpatialFilterStore((store) => store.resetSpatialFilters);

  const query = useQuery({
    queryKey: ["spatial-intelligence", projectId, scenarioId, workflow?.status],
    queryFn: async () => {
      const [summary, executionActions] = await Promise.all([
        settle(getProjectSpatialSummary(projectId)),
        settle(listProjectExecutionActions(projectId, scenarioId)),
      ]);
      return summary || fallbackSpatialSummary(workflow, executionActions?.actions || []);
    },
    staleTime: 60_000,
    placeholderData: (previousData) => previousData,
  });

  return {
    ...query,
    project,
    workflow,
    filters,
    setSpatialFilter,
    resetSpatialFilters,
  };
}
