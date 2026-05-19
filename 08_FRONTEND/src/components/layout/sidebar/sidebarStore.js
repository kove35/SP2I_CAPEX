import { create } from "zustand";
import { persist } from "zustand/middleware";
import { PROJECT_CONTEXT, SCENARIO_OPTIONS } from "../../../utils/businessContext";

const defaultOpenedSections = ["direction", "dqe"];

export const useSidebarStore = create(
  persist(
    (set) => ({
      isCollapsed: false,
      isMobileOpen: false,
      openedSections: defaultOpenedSections,
      activeProject: PROJECT_CONTEXT.code,
      activeScenario: SCENARIO_OPTIONS[0].code,
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
      setProjectContext: ({ project, scenario }) =>
        set((state) => ({
          activeProject: project || state.activeProject,
          activeScenario: scenario || state.activeScenario,
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
      }),
    }
  )
);
