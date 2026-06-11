import React from "react";
import { Activity, AlertTriangle, Database, Gauge, LineChart, PackageCheck, PiggyBank, TrendingUp } from "lucide-react";
import AdvancedKpiCard from "../analytics/kpi/AdvancedKpiCard";
import { formatMoney, formatPercent } from "../../shared/formatters";
import Skeleton from "../../ui/Skeleton";

export default function EnterpriseKpiGrid({ kpis = {}, loading = false }) {
  const economyRate = Number(kpis.taux_economie || 0) * 100;
  const importRate = Number(kpis.taux_importable || 0) * 100;
  const confidence = kpis.analytics_confidence_label || "Moyenne";
  const capexOptimise = Number(kpis.capex_optimise || 0);
  const nbLignes = Number(kpis.nb_lignes || 0);
  const nbLots = Number(kpis.nb_lots || 0);
  const roiValues = [Number(kpis.roi_import || 0), Number(kpis.taux_economie || 0)].filter((value) => Number.isFinite(value));
  const roiAverage = roiValues.length ? roiValues.reduce((sum, value) => sum + value, 0) / roiValues.length : 0;
  const roiMax = roiValues.length ? Math.max(...roiValues) : 0;
  const roiMin = roiValues.length ? Math.min(...roiValues) : 0;
  const displayRisk = kpis.analytics_confidence === "LOW" && ["Fort", "Eleve", "Elevé", "Critique"].includes(String(kpis.risque_global || ""))
    ? "Moyen"
    : (kpis.risque_global || "Moyen");

  React.useEffect(() => {
    console.log("EnterpriseKpiGrid render", { nb_lignes: kpis.nb_lignes, kpis });
  }, [kpis.nb_lignes]);
  const items = [
    { label: "Budget initial", value: formatMoney(kpis.capex_brut || kpis.capex_local), helper: "Reference locale", tone: "blue", icon: Database, delta: 0, points: [71, 72, 74, 76, 75, 78, 80] },
    { label: "Budget optimise", value: formatMoney(kpis.capex_optimise), helper: "Apres arbitrage", tone: "green", icon: LineChart, delta: -economyRate, positiveIsGood: false, points: [80, 78, 74, 72, 70, 68, 66] },
    { label: "Economie nette", value: formatMoney(kpis.economie_nette || kpis.economie), helper: "Gain potentiel", tone: "amber", icon: PiggyBank, delta: economyRate, points: [18, 24, 28, 36, 41, 48, 55] },
    { label: "ROI import", value: formatPercent(kpis.roi_import), helper: "Retour import", tone: "cyan", icon: TrendingUp, delta: Number(kpis.roi_import || 0) * 100, points: [21, 24, 25, 31, 36, 42, 48] },
    { label: "Taux economie", value: formatPercent(kpis.taux_economie), helper: "Sur budget initial", tone: "green", icon: Gauge, delta: economyRate, points: [12, 18, 20, 26, 31, 38, 44] },
    { label: "Lignes analysées", value: Number(kpis.nb_lignes || 0).toLocaleString("fr-FR"), helper: "Postes synchronisés", tone: "blue", icon: PackageCheck, delta: kpis.nb_lignes ? 100 : 0, points: [12, 24, 38, 52, 66, 82, 100] },
    { label: "Risque global", value: displayRisk, helper: confidence === "Faible" ? "Limite par confiance faible" : "Aide a la decision", tone: "amber", icon: AlertTriangle, delta: -4.2, positiveIsGood: false, points: [62, 60, 58, 59, 55, 53, 50] },
    { label: "Taux importable", value: formatPercent(kpis.taux_importable), helper: "Import/local", tone: "cyan", icon: Activity, delta: importRate, points: [32, 38, 41, 48, 57, 65, 70] },
    { label: "Confiance analyse", value: confidence, helper: `${nbLignes.toLocaleString("fr-FR")} lignes / ${nbLots.toLocaleString("fr-FR")} lots`, tone: confidence === "Faible" ? "amber" : confidence === "Elevee" ? "green" : "blue", icon: Gauge, delta: Number(kpis.analytics_confidence_score || 0), points: [35, 48, 61, 66, 74, 82, 90] },
    { label: "CAPEX / lot", value: formatMoney(nbLots ? capexOptimise / nbLots : 0), helper: "Budget optimise moyen", tone: "blue", icon: Database, delta: 0, points: [31, 35, 42, 45, 50, 54, 58] },
    { label: "CAPEX / ligne", value: formatMoney(nbLignes ? capexOptimise / nbLignes : 0), helper: "Approximation par poste", tone: "cyan", icon: PackageCheck, delta: 0, points: [18, 22, 29, 35, 38, 42, 46] },
    { label: "ROI moyen", value: formatPercent(roiAverage), helper: "ROI import / economie", tone: "green", icon: TrendingUp, delta: roiAverage * 100, points: [10, 14, 18, 23, 27, 31, 35] },
    { label: "ROI maximal", value: formatPercent(roiMax), helper: "Meilleur signal KPI", tone: "green", icon: TrendingUp, delta: roiMax * 100, points: [12, 19, 24, 31, 36, 42, 49] },
    { label: "ROI minimal", value: formatPercent(roiMin), helper: "Signal prudent", tone: "amber", icon: Gauge, delta: roiMin * 100, points: [8, 12, 16, 20, 23, 28, 32] },
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
