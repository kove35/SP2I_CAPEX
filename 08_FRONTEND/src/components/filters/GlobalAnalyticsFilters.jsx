import React from "react";
import { RotateCcw, Search, X } from "lucide-react";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";

const fields = [
  ["batiment", "Batiment", "Tous"],
  ["niveau", "Niveau", "Tous"],
  ["lot", "Lot", "Tous"],
  ["famille", "Famille", "Toutes"],
  ["decisionImport", "Import/local", "Tous"],
];

export default function GlobalAnalyticsFilters() {
  const { filters, activeChips, applyFilter, clearFilter, reset } = useCrossFiltering();

  return (
    <section className="global-analytics-panel" aria-label="Filtres globaux analytics">
      <div className="global-analytics-filters">
        <label className="filter-project">
          <span>Projet</span>
          <input value={filters.projet || ""} onChange={(event) => applyFilter("projet", event.target.value)} />
        </label>
        <label className="filter-project">
          <span>Scenario</span>
          <input value={filters.scenario || ""} onChange={(event) => applyFilter("scenario", event.target.value)} />
        </label>
        {fields.map(([key, label, placeholder]) => (
          <label key={key}>
            <span>{label}</span>
            <input value={filters[key] || ""} onChange={(event) => applyFilter(key, event.target.value)} placeholder={placeholder} />
          </label>
        ))}
        <label>
          <span>Debut</span>
          <input type="date" value={filters.periodeDebut || ""} onChange={(event) => applyFilter("periodeDebut", event.target.value)} />
        </label>
        <label>
          <span>Fin</span>
          <input type="date" value={filters.periodeFin || ""} onChange={(event) => applyFilter("periodeFin", event.target.value)} />
        </label>
        <button type="button" className="icon-text-button" onClick={reset}>
          <RotateCcw size={15} />
          Reset
        </button>
        <div className="filter-live-chip">
          <Search size={14} />
          Cross-filter actif
        </div>
      </div>

      {activeChips.length ? (
        <div className="filter-chip-row" aria-label="Filtres actifs">
          {activeChips.map((chip) => (
            <button key={chip.key} type="button" onClick={() => clearFilter(chip.key)}>
              <span>{chip.label}</span>
              <strong>{chip.value}</strong>
              <X size={13} />
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
