import { create } from "zustand";

export const useSpatialFilterStore = create((set) => ({
  filters: {
    batiment: "",
    niveau: "",
    appart: "",
    piece: "",
    zone: "",
  },
  setSpatialFilter: (key, value) =>
    set((state) => ({
      filters: {
        ...state.filters,
        [key]: value,
      },
    })),
  resetSpatialFilters: () =>
    set({
      filters: {
        batiment: "",
        niveau: "",
        appart: "",
        piece: "",
        zone: "",
      },
    }),
}));

