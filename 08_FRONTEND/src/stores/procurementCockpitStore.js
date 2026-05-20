import { create } from "zustand";

export const useProcurementCockpitStore = create((set) => ({
  activeDashboard: "direction",
  selectedLot: "",
  selectedFamily: "",
  selectedSupplier: "",
  selectedLine: null,
  viewMode: "executive",
  setActiveDashboard: (activeDashboard) => set({ activeDashboard }),
  setSelection: (selection) => set(selection),
  setSelectedLine: (selectedLine) => set({ selectedLine }),
  setViewMode: (viewMode) => set({ viewMode }),
  resetCockpitSelection: () => set({
    selectedLot: "",
    selectedFamily: "",
    selectedSupplier: "",
    selectedLine: null,
  }),
}));
