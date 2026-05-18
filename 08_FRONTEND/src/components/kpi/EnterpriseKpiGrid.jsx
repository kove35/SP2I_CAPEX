import React from "react";
import { Activity, AlertTriangle, Database, Gauge, LineChart, PackageCheck, PiggyBank, TrendingUp } from "lucide-react";
import AdvancedKpiCard from "../analytics/kpi/AdvancedKpiCard";
import { formatMoney, formatPercent } from "../../shared/formatters";
import Skeleton from "../../ui/Skeleton";

export default function EnterpriseKpiGrid({ kpis = {}, loading = false }) {
  const economyRate = Number(kpis.taux_economie || 0) * 100;
  const importRate = Number(kpis.taux_importable || 0) * 100;
  const items = [
    { label: "CAPEX brut", value: formatMoney(kpis.capex_brut || kpis.capex_local), helper: "Reference locale", tone: "blue", icon: Database, delta: 0, points: [71, 72, 74, 76, 75, 78, 80] },
    { label: "CAPEX optimise", value: formatMoney(kpis.capex_optimise), helper: "Apres arbitrage", tone: "green", icon: LineChart, delta: -economyRate, positiveIsGood: false, points: [80, 78, 74, 72, 70, 68, 66] },
    { label: "Economie nette", value: formatMoney(kpis.economie_nette || kpis.economie), helper: "Gain potentiel", tone: "amber", icon: PiggyBank, delta: economyRate, points: [18, 24, 28, 36, 41, 48, 55] },
    { label: "ROI import", value: formatPercent(kpis.roi_import), helper: "Retour import", tone: "cyan", icon: TrendingUp, delta: Number(kpis.roi_import || 0) * 100, points: [21, 24, 25, 31, 36, 42, 48] },
    { label: "Taux economie", value: formatPercent(kpis.taux_economie), helper: "Sur CAPEX brut", tone: "green", icon: Gauge, delta: economyRate, points: [12, 18, 20, 26, 31, 38, 44] },
    { label: "Lignes DQE", value: Number(kpis.nb_lignes || 0).toLocaleString("fr-FR"), helper: "FACT_METRE", tone: "blue", icon: PackageCheck, delta: kpis.nb_lignes ? 100 : 0, points: [12, 24, 38, 52, 66, 82, 100] },
    { label: "Risque global", value: kpis.risque_global || "Moyen", helper: "Decision intelligence", tone: "amber", icon: AlertTriangle, delta: -4.2, positiveIsGood: false, points: [62, 60, 58, 59, 55, 53, 50] },
    { label: "Taux importable", value: formatPercent(kpis.taux_importable), helper: "Import/local", tone: "cyan", icon: Activity, delta: importRate, points: [32, 38, 41, 48, 57, 65, 70] },
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
        <AdvancedKpiCard key={item.label} {...item} />
      ))}
    </section>
  );
}
