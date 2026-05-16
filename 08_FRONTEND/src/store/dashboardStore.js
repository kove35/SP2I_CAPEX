import { create } from "zustand";

const defaultFilters = {
  projet: "Pointe-Noire CAPEX",
  scenario: "FRONT_COCKPIT_TEST",
  batiment: "",
  niveau: "",
  lot: "",
  famille: "",
  fournisseur: "",
  decisionImport: "",
  periode: "",
};

export const useDashboardStore = create((set) => ({
  filters: defaultFilters,
  activeProject: defaultFilters.projet,
  activeScenario: defaultFilters.scenario,
  capexParameters: {
    transport: 0.12,
    douane: 0.15,
    margeImport: 0.18,
    seuilDecisionImport: 0.97,
  },
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
      activeProject: key === "projet" ? value : state.activeProject,
      activeScenario: key === "scenario" ? value : state.activeScenario,
    })),
  resetFilters: () =>
    set({
      filters: defaultFilters,
      activeProject: defaultFilters.projet,
      activeScenario: defaultFilters.scenario,
    }),
  setCapexParameters: (values) =>
    set((state) => ({
      capexParameters: { ...state.capexParameters, ...values },
    })),
}));
