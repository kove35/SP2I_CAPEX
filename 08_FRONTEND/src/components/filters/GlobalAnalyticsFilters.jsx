import React from "react";
import { useQuery } from "@tanstack/react-query";
import { RotateCcw, Search, X } from "lucide-react";
import { useCrossFiltering } from "../../hooks/useCrossFiltering";
import { getAnalyticsFilters } from "../../services/filterService";
import { getProjectContext, getScenarioContext, SCENARIO_OPTIONS } from "../../utils/businessContext";
import AnalyticsSelect from "./AnalyticsSelect";

const selectFields = [
  ["batiment", "Batiment", "Tous", "batiments"],
  ["niveau", "Niveau", "Tous", "niveaux"],
  ["lot", "Lot", "Tous", "lots"],
  ["famille", "Famille", "Toutes", "familles"],
  ["importLocal", "Import/local", "Tous", "importLocal"],
];

export default function GlobalAnalyticsFilters() {
  const { filters, activeChips, applyFilter, clearFilter, reset } = useCrossFiltering();
  const project = getProjectContext(filters.projet);
  const scenario = getScenarioContext(filters.scenario);
  const filterOptions = useQuery({
    queryKey: ["analytics-filter-options"],
    queryFn: getAnalyticsFilters,
    staleTime: 5 * 60_000,
  });
  const options = filterOptions.data || {};

  return (
    <section className="global-analytics-panel" aria-label="Filtres de pilotage">
      <div className="global-analytics-filters">
        <div className="decision-context-card project-context-card">
          <span>Projet immobilier</span>
          <strong>{project.label}</strong>
          <small>{project.type} · {project.location}</small>
        </div>
        <label className={`scenario-select-field ${scenario.tone}`}>
          <span>Strategie active</span>
          <select value={scenario.code} onChange={(event) => applyFilter("scenario", event.target.value)}>
            {SCENARIO_OPTIONS.map((option) => (
              <option key={option.code} value={option.code}>{option.label}</option>
            ))}
          </select>
          <small>{scenario.description}</small>
        </label>
        {selectFields.map(([key, label, placeholder, optionKey]) => (
          <AnalyticsSelect
            key={key}
            label={label}
            value={filters[key] || ""}
            options={options[optionKey] || []}
            placeholder={placeholder}
            loading={filterOptions.isLoading}
            onChange={(nextValue) => applyFilter(key, nextValue)}
          />
        ))}
        <label>
          <span>Debut</span>
          <input type="date" value={filters.dateDebut || ""} onChange={(event) => applyFilter("dateDebut", event.target.value)} />
        </label>
        <label>
          <span>Fin</span>
          <input type="date" value={filters.dateFin || ""} onChange={(event) => applyFilter("dateFin", event.target.value)} />
        </label>
        <button type="button" className="icon-text-button" onClick={reset}>
          <RotateCcw size={15} />
          Reinitialiser
        </button>
        <div className="filter-live-chip">
          <Search size={14} />
          Filtres synchronises
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
