import { create } from "zustand";

export const defaultAnalyticsFilters = {
  projet: "Pointe-Noire CAPEX",
  scenario: "FRONT_COCKPIT_TEST",
  batiment: "",
  niveau: "",
  lot: "",
  famille: "",
  fournisseur: "",
  importLocal: "",
  decisionImport: "",
  dateDebut: "",
  dateFin: "",
  periodeDebut: "",
  periodeFin: "",
};

export const analyticsFilterLabels = {
  projet: "Projet",
  scenario: "Scenario",
  batiment: "Batiment",
  niveau: "Niveau",
  lot: "Lot",
  famille: "Famille",
  fournisseur: "Fournisseur",
  importLocal: "Import/local",
  decisionImport: "Import/local",
  dateDebut: "Debut",
  dateFin: "Fin",
  periodeDebut: "Debut",
  periodeFin: "Fin",
};

function cleanFilters(filters) {
  const normalizedAliases = {
    ...filters,
    decisionImport: filters.decisionImport || filters.importLocal || "",
    importLocal: filters.importLocal || filters.decisionImport || "",
    periodeDebut: filters.periodeDebut || filters.dateDebut || "",
    dateDebut: filters.dateDebut || filters.periodeDebut || "",
    periodeFin: filters.periodeFin || filters.dateFin || "",
    dateFin: filters.dateFin || filters.periodeFin || "",
  };
  return Object.fromEntries(
    Object.entries({ ...defaultAnalyticsFilters, ...normalizedAliases }).map(([key, value]) => [
      key,
      typeof value === "string" ? value.trim() : value || "",
    ])
  );
}

export const useAnalyticsFilterStore = create((set, get) => ({
  filters: defaultAnalyticsFilters,
  revision: 0,
  setFilter: (key, value) =>
    set((state) => ({
      filters: cleanFilters({ ...state.filters, [key]: value }),
      revision: state.revision + 1,
    })),
  setFilters: (values) =>
    set((state) => ({
      filters: cleanFilters({ ...state.filters, ...values }),
      revision: state.revision + 1,
    })),
  replaceFilters: (values) =>
    set((state) => ({
      filters: cleanFilters(values),
      revision: state.revision + 1,
    })),
  resetFilters: () =>
    set((state) => ({
      filters: defaultAnalyticsFilters,
      revision: state.revision + 1,
    })),
  getActiveFilters: () =>
    Object.entries(get().filters).filter(([key, value]) => {
      if (!value) return false;
      return value !== defaultAnalyticsFilters[key];
    }),
}));
