import React from "react";
import { RotateCcw, Search } from "lucide-react";
import { useDashboardStore } from "../../store/dashboardStore";

const fields = [
  ["batiment", "Bâtiment", "Tous"],
  ["niveau", "Niveau", "Tous"],
  ["lot", "Lot", "Tous"],
  ["famille", "Famille", "Toutes"],
  ["decisionImport", "Import/local", "Tous"],
];

export default function GlobalAnalyticsFilters() {
  const filters = useDashboardStore((state) => state.filters);
  const setFilter = useDashboardStore((state) => state.setFilter);
  const resetFilters = useDashboardStore((state) => state.resetFilters);

  return (
    <section className="global-analytics-filters" aria-label="Filtres globaux analytics">
      <label className="filter-project">
        <span>Projet</span>
        <input value={filters.projet || ""} onChange={(event) => setFilter("projet", event.target.value)} />
      </label>
      <label className="filter-project">
        <span>Scénario</span>
        <input value={filters.scenario || ""} onChange={(event) => setFilter("scenario", event.target.value)} />
      </label>
      {fields.map(([key, label, placeholder]) => (
        <label key={key}>
          <span>{label}</span>
          <input
            value={filters[key] || ""}
            onChange={(event) => setFilter(key, event.target.value)}
            placeholder={placeholder}
          />
        </label>
      ))}
      <label>
        <span>Début</span>
        <input type="date" value={filters.periodeDebut || ""} onChange={(event) => setFilter("periodeDebut", event.target.value)} />
      </label>
      <label>
        <span>Fin</span>
        <input type="date" value={filters.periodeFin || ""} onChange={(event) => setFilter("periodeFin", event.target.value)} />
      </label>
      <button type="button" className="icon-text-button" onClick={resetFilters}>
        <RotateCcw size={15} />
        Reset
      </button>
      <div className="filter-live-chip">
        <Search size={14} />
        Cross-filter actif
      </div>
    </section>
  );
}
