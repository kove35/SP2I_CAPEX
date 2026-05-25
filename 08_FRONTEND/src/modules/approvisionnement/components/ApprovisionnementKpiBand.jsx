import React from "react";
import { AlertTriangle, Boxes, Clock3, PackageCheck, Ship, Truck, Users, WalletCards } from "lucide-react";
import { formatMoney } from "../../../shared/formatters";

const ITEMS = [
  { key: "committedBudget", label: "Budget engagé", icon: WalletCards, format: formatMoney, tone: "green" },
  { key: "launchedOrders", label: "Commandes lancées", icon: PackageCheck, suffix: "", tone: "blue" },
  { key: "criticalOrders", label: "Commandes critiques", icon: AlertTriangle, suffix: "", tone: "amber" },
  { key: "activeSuppliers", label: "Fournisseurs actifs", icon: Users, suffix: "", tone: "cyan" },
  { key: "averageEta", label: "Délai moyen", icon: Clock3, format: (value) => `${Math.round(Number(value || 0))} j`, tone: "violet" },
  { key: "riskScore", label: "Risque global", icon: Truck, format: (value) => `${Math.round(Number(value || 0))}/100`, tone: "amber" },
  { key: "blockingLots", label: "Lots bloquants", icon: Boxes, suffix: "", tone: "red" },
  { key: "containers", label: "Containers estimés", icon: Ship, suffix: "", tone: "blue" },
];

function valueFor(item, value) {
  if (item.format) return item.format(value);
  return Number(value || 0).toLocaleString("fr-FR");
}

export default function ApprovisionnementKpiBand({ kpis = {} }) {
  return (
    <section className="appro-kpi-band" aria-label="KPI approvisionnement">
      {ITEMS.map((item) => {
        const Icon = item.icon;
        return (
          <article className={`appro-kpi-card tone-${item.tone}`} key={item.key}>
            <span><Icon size={15} /> {item.label}</span>
            <strong>{valueFor(item, kpis[item.key])}</strong>
          </article>
        );
      })}
    </section>
  );
}
