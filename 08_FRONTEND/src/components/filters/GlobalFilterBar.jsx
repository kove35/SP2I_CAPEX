import React from "react";
import { RotateCcw } from "lucide-react";
import { useDashboardStore } from "../../store/dashboardStore";

const filterConfig = [
  ["projet", "Projet"],
  ["scenario", "Scenario"],
  ["batiment", "Batiment"],
  ["niveau", "Niveau"],
  ["lot", "Lot"],
  ["famille", "Famille"],
  ["decisionImport", "Import/local"],
];

export default function GlobalFilterBar() {
  const filters = useDashboardStore((state) => state.filters);
  const setFilter = useDashboardStore((state) => state.setFilter);
  const resetFilters = useDashboardStore((state) => state.resetFilters);

  return (
    <section className="global-filter-bar" aria-label="Filtres globaux dashboard">
      {filterConfig.map(([key, label]) => (
        <label key={key}>
          <span>{label}</span>
          <input
            value={filters[key] || ""}
            onChange={(event) => setFilter(key, event.target.value)}
            placeholder={label}
          />
        </label>
      ))}
      <button type="button" className="icon-text-button" onClick={resetFilters}>
        <RotateCcw size={15} />
        Reset
      </button>
    </section>
  );
}
