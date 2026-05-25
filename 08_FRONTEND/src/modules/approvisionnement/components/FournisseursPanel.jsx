import React from "react";
import { ShieldCheck, TriangleAlert } from "lucide-react";
import { formatMoney } from "../../../shared/formatters";

export default function FournisseursPanel({ suppliers = [], onSupplier }) {
  return (
    <article className="appro-panel">
      <header className="appro-panel-header">
        <div>
          <span>Fournisseurs</span>
          <strong>Fiabilité et dépendance critique</strong>
        </div>
      </header>
      <div className="appro-supplier-list">
        {suppliers.slice(0, 8).map((supplier) => (
          <button type="button" key={supplier.name} onClick={() => onSupplier?.(supplier)} className="appro-supplier-card">
            <div>
              <strong>{supplier.name}</strong>
              <span>{supplier.country} · {supplier.category}</span>
            </div>
            <div className="appro-score-line">
              <i style={{ width: `${Math.min(Math.max(supplier.trustScore, 8), 100)}%` }} />
            </div>
            <footer>
              <span><ShieldCheck size={13} /> {supplier.trustScore}/100</span>
              <span>{Math.round(supplier.averageEta)} j</span>
              <span>{formatMoney(supplier.amount)}</span>
            </footer>
            <em className={supplier.dependency.includes("critique") ? "warning" : "stable"}>
              {supplier.dependency.includes("critique") ? <TriangleAlert size={13} /> : <ShieldCheck size={13} />}
              {supplier.dependency}
            </em>
          </button>
        ))}
        {!suppliers.length ? <p className="appro-empty">Aucun fournisseur consolidé pour le moment.</p> : null}
      </div>
    </article>
  );
}
