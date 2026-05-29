import React from "react";

function formatSyncTimestamp(value) {
  if (!value) return "Aucune synchronisation";
  try {
    return new Date(value).toLocaleString("fr-FR");
  } catch {
    return String(value);
  }
}

function safeCount(value) {
  const numeric = Number(value);
  if (Number.isFinite(numeric)) return numeric.toLocaleString("fr-FR");
  if (value == null || value === "") return "-";
  return String(value);
}

export default function DataLineageCard({
  eyebrow = "Qualité de synchronisation",
  title,
  badge = "A vérifier",
  badgeTone = "warning",
  metrics = [],
  testId,
}) {
  const badgeClass = `data-lineage-status-badge ${badgeTone}`;

  return (
    <section className="data-lineage-card" data-testid={testId}>
      <div className="data-lineage-card-header">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        <span className={badgeClass}>{badge}</span>
      </div>

      <div className="data-lineage-grid">
        {metrics.map((metric) => (
          <article className="data-lineage-stat" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.detail ?? "-"}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

export function buildLineageMetric(label, value, detail) {
  return {
    label,
    value: safeCount(value),
    detail: detail ?? "-",
  };
}

export function formatLineageSync(value) {
  return formatSyncTimestamp(value);
}
