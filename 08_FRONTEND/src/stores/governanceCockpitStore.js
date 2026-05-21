import { create } from "zustand";

export const useGovernanceCockpitStore = create((set) => ({
  selectedReferenceId: "",
  filters: {
    family: "",
    priority: "",
    escalation: "",
    status: "",
  },
  setSelectedReferenceId: (selectedReferenceId) => set({ selectedReferenceId }),
  setFilter: (key, value) => set((state) => ({
    filters: {
      ...state.filters,
      [key]: value,
    },
  })),
  resetFilters: () => set({
    selectedReferenceId: "",
    filters: {
      family: "",
      priority: "",
      escalation: "",
      status: "",
    },
  }),
}));
