import React from "react";
import AppShell from "../layouts/AppShell";
import LandingPage from "../marketing/LandingPage";
import AnalyticsPage from "../modules/analytics/AnalyticsPage";
import CockpitPage from "../modules/cockpit/CockpitPage";
import DqePage from "../modules/dqe/DqePage";
import LogisticsPage from "../modules/logistics/LogisticsPage";
import ProcurementPage from "../modules/procurement/ProcurementPage";
import SimulationPage from "../modules/simulation/SimulationPage";
import SiteExecutionPage from "../modules/chantier/SiteExecutionPage";

const ProcurementIntelligenceCockpit = React.lazy(() => import("../modules/procurementCockpit/ProcurementIntelligenceCockpit"));

const cockpitRoutes = {
  "/app": <CockpitPage />,
  "/app/simulation": <SimulationPage />,
  "/app/procurement": <ProcurementPage />,
  "/app/procurement-intelligence": (
    <React.Suspense fallback={<div className="live-refresh">Chargement du cockpit procurement...</div>}>
      <ProcurementIntelligenceCockpit />
    </React.Suspense>
  ),
  "/app/logistics": <LogisticsPage />,
  "/app/site": <SiteExecutionPage />,
  "/app/dqe": <DqePage />,
  "/app/analytics": <AnalyticsPage />,
};

export function navigateTo(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export default function AppRouter() {
  const [path, setPath] = React.useState(`${window.location.pathname}${window.location.search}`);

  React.useEffect(() => {
    const syncPath = () => setPath(`${window.location.pathname}${window.location.search}`);
    window.addEventListener("popstate", syncPath);
    return () => window.removeEventListener("popstate", syncPath);
  }, []);

  const routePath = window.location.pathname;
  const searchParams = new URLSearchParams(window.location.search);

  if (routePath === "/" || routePath === "/marketing") {
    return <LandingPage onNavigate={navigateTo} />;
  }

  const page = routePath === "/app/simulation"
    ? <SimulationPage defaultTab={searchParams.get("tab") || "simulation"} />
    : cockpitRoutes[routePath] || <CockpitPage />;

  return <AppShell activePath={path} onNavigate={navigateTo}>{page}</AppShell>;
}
