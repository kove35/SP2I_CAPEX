import React from "react";
import { buildSpatialOptions } from "../adapters/spatialAdapter";
import { spatialMaturityLabel } from "../utils/spatialFormatters";
import SpatialBreadcrumb from "./SpatialBreadcrumb";

function SpatialSelect({ label, value, options, onChange }) {
  if (!options.length) return null;
  return (
    <label className="spatial-filter-field">
      <span>{label}</span>
      <select value={value || ""} onChange={(event) => onChange(event.target.value)}>
        <option value="">Tous</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function SpatialDrilldownPanel({ summary, filters, onFilterChange, onReset }) {
  const options = React.useMemo(() => buildSpatialOptions(summary), [summary]);
  const maturity = summary?.maturity || {};
  const mode = maturity.mode || maturity.maturity || "NON_BIM";
  const isBimReady = mode === "BIM_READY";
  const isSpatial = mode !== "NON_BIM" || Number(summary?.kpis?.spatialized_lines_count || 0) > 0;

  if (!isSpatial) return null;

  return (
    <section className="spatial-panel spatial-drilldown-panel" data-testid="spatial-drilldown-panel">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Spatial Intelligence</p>
          <h3>Drilldown chantier</h3>
        </div>
        <span className="spatial-mode-badge">{spatialMaturityLabel(maturity)}</span>
      </div>

      <SpatialBreadcrumb
        items={[filters.batiment, filters.niveau, filters.appart, filters.piece]}
      />

      <div className="spatial-filter-grid">
        <SpatialSelect label="Bâtiment" value={filters.batiment} options={options.batiments} onChange={(value) => onFilterChange("batiment", value)} />
        <SpatialSelect label="Niveau" value={filters.niveau} options={options.niveaux} onChange={(value) => onFilterChange("niveau", value)} />
        {isBimReady ? (
          <SpatialSelect label="Appartement" value={filters.appart} options={options.apparts} onChange={(value) => onFilterChange("appart", value)} />
        ) : null}
        <SpatialSelect label="Pièce" value={filters.piece} options={options.pieces} onChange={(value) => onFilterChange("piece", value)} />
      </div>

      <button type="button" className="spatial-link-action" onClick={onReset}>
        Réinitialiser les filtres spatiaux
      </button>
    </section>
  );
}

