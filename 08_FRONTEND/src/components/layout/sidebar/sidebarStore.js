import { create } from "zustand";
import { persist } from "zustand/middleware";
import { PROJECT_CONTEXT, SCENARIO_OPTIONS } from "../../../utils/businessContext";

const defaultOpenedSections = ["general", "workspace", "other"];

function buildProjectMeta(projectDetails, fallbackProject) {
  const resolvedProject = projectDetails || fallbackProject;
  const fallback = resolvedProject || {};
  return {
    code: fallback.workspace_key || fallback.code || fallback.id || PROJECT_CONTEXT.code,
    label: fallback.name || fallback.label || PROJECT_CONTEXT.label,
    location: [fallback.city, fallback.country].filter(Boolean).join(", ") || PROJECT_CONTEXT.location,
    type: fallback.type || PROJECT_CONTEXT.type,
    status: fallback.status || PROJECT_CONTEXT.status,
    trust_score: fallback.trust_score ?? null,
    details: resolvedProject || null,
  };
}

export const useSidebarStore = create(
  persist(
    (set) => ({
      isCollapsed: false,
      isMobileOpen: false,
      openedSections: defaultOpenedSections,
      activeProject: PROJECT_CONTEXT.code,
      activeScenario: SCENARIO_OPTIONS[0].code,
      projectMeta: buildProjectMeta(null, null),
      apiStatus: "online",
      syncStatus: "pret",
      toggleCollapsed: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
      setCollapsed: (value) => set({ isCollapsed: value }),
      openMobile: () => set({ isMobileOpen: true }),
      closeMobile: () => set({ isMobileOpen: false }),
      toggleMobile: () => set((state) => ({ isMobileOpen: !state.isMobileOpen })),
      toggleSection: (sectionId) =>
        set((state) => {
          const opened = new Set(state.openedSections);
          if (opened.has(sectionId)) {
            opened.delete(sectionId);
          } else {
            opened.add(sectionId);
          }
          return { openedSections: [...opened] };
        }),
      setProjectContext: ({ project, scenario, projectDetails }) =>
        set((state) => ({
          activeProject: project || state.activeProject,
          activeScenario: scenario || state.activeScenario,
          projectMeta: buildProjectMeta(projectDetails, state.projectMeta?.details || null),
        })),
      setStatuses: ({ apiStatus, syncStatus }) =>
        set((state) => ({
          apiStatus: apiStatus || state.apiStatus,
          syncStatus: syncStatus || state.syncStatus,
        })),
    }),
    {
      name: "sp2i-sidebar",
      partialize: (state) => ({
        isCollapsed: state.isCollapsed,
        openedSections: state.openedSections,
        projectMeta: state.projectMeta,
      }),
    }
  )
);
