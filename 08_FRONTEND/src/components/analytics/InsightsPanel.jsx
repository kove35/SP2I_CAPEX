import React from "react";
import { Brain, CircleDollarSign, Gauge, Layers3 } from "lucide-react";
import { formatMoney, formatPercent } from "../../shared/formatters";

export default function InsightsPanel({ kpis = {}, barRows = [], table = [] }) {
  const topLot = [...barRows].sort((a, b) => Number(b.capex_brut || 0) - Number(a.capex_brut || 0))[0];
  const capex = Number(kpis.capex_brut || 0);
  const topLotShare = capex && topLot ? Number(topLot.capex_brut || 0) / capex : 0;
  const importRows = table.filter((row) => String(row.decision_import || "").toUpperCase() === "IMPORT");
  const localRows = table.filter((row) => String(row.decision_import || "").toUpperCase() === "LOCAL");

  const insights = [
    {
      icon: CircleDollarSign,
      label: "Optimisation CAPEX",
      text: `Les arbitrages import/local generent ${formatMoney(kpis.economie_nette || kpis.economie)} d'economie nette.`,
    },
    {
      icon: Layers3,
      label: "Concentration lot",
      text: topLot
        ? `${topLot.label || topLot.lot} concentre ${formatPercent(topLotShare)} du CAPEX brut.`
        : "Les donnees par lot seront visibles apres synchronisation.",
    },
    {
      icon: Gauge,
      label: "Importabilite",
      text: `${formatPercent(kpis.taux_importable)} du portefeuille est candidat a l'analyse import.`,
    },
    {
      icon: Brain,
      label: "Decision intelligence",
      text: `${importRows.length} lignes en decision IMPORT et ${localRows.length} lignes conservees en LOCAL dans le preview courant.`,
    },
  ];

  return (
    <aside className="insights-panel">
      <header>
        <span>SP2I Decision Intelligence</span>
        <strong>Insights executifs</strong>
      </header>
      <div>
        {insights.map(({ icon: Icon, label, text }) => (
          <article key={label}>
            <Icon size={16} />
            <div>
              <strong>{label}</strong>
              <p>{text}</p>
            </div>
          </article>
        ))}
      </div>
    </aside>
  );
}
