import React from "react";
import { Activity, AlertTriangle, Database, Gauge, LineChart, PackageCheck, PiggyBank, TrendingUp } from "lucide-react";
import Skeleton from "../../ui/Skeleton";
import { formatMoney, formatPercent } from "../../shared/formatters";
import EnterpriseKpiCard from "./EnterpriseKpiCard";

export default function EnterpriseKpiGrid({ kpis = {}, loading = false }) {
  const items = [
    { label: "CAPEX brut", value: formatMoney(kpis.capex_brut || kpis.capex_local), helper: "Base locale", tone: "blue", icon: Database },
    { label: "CAPEX optimise", value: formatMoney(kpis.capex_optimise), helper: "Après arbitrage", tone: "green", icon: LineChart },
    { label: "Economie nette", value: formatMoney(kpis.economie_nette || kpis.economie), helper: "Gain potentiel", tone: "amber", icon: PiggyBank },
    { label: "ROI import", value: formatPercent(kpis.roi_import), helper: "Retour import", tone: "cyan", icon: TrendingUp },
    { label: "Taux économie", value: formatPercent(kpis.taux_economie), helper: "Sur CAPEX brut", tone: "green", icon: Gauge },
    { label: "Lignes DQE", value: Number(kpis.nb_lignes || 0).toLocaleString("fr-FR"), helper: "FACT_METRE", tone: "blue", icon: PackageCheck },
    { label: "Risque global", value: kpis.risque_global || "Moyen", helper: "Decision intelligence", tone: "amber", icon: AlertTriangle },
    { label: "Taux importable", value: formatPercent(kpis.taux_importable), helper: "Import/local", tone: "cyan", icon: Activity },
  ];

  if (loading) {
    return (
      <section className="enterprise-kpi-grid">
        {items.map((item) => (
          <article key={item.label} className="enterprise-kpi">
            <Skeleton rows={2} />
          </article>
        ))}
      </section>
    );
  }

  return (
    <section className="enterprise-kpi-grid">
      {items.map((item) => (
        <EnterpriseKpiCard key={item.label} {...item} />
      ))}
    </section>
  );
}
