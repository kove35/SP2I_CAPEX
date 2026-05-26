import React from "react";

export default function SpatialBreadcrumb({ items = [], current = "" }) {
  const visibleItems = items.filter(Boolean);
  if (!visibleItems.length && !current) return null;

  return (
    <nav className="spatial-breadcrumb" aria-label="Fil d'Ariane spatial">
      <span>Projet</span>
      {visibleItems.map((item) => (
        <React.Fragment key={item}>
          <i aria-hidden="true">›</i>
          <span>{item}</span>
        </React.Fragment>
      ))}
      {current ? (
        <>
          <i aria-hidden="true">›</i>
          <strong>{current}</strong>
        </>
      ) : null}
    </nav>
  );
}

