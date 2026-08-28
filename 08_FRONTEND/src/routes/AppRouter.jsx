import React from "react";
import AppShell from "../layouts/AppShell";
import LandingPage from "../marketing/LandingPage";

const AnalyticsPage = React.lazy(() => import("../modules/analytics/AnalyticsPage"));
const ApprovisionnementDashboard = React.lazy(() => import("../modules/approvisionnement/pages/ApprovisionnementDashboard"));
const CockpitPage = React.lazy(() => import("../modules/cockpit/CockpitPage"));
const DqePage = React.lazy(() => import("../modules/dqe/DqePage"));
const ProcurementIntelligenceCockpit = React.lazy(() => import("../modules/procurementCockpit/ProcurementIntelligenceCockpit"));
const GovernanceCockpit = React.lazy(() => import("../modules/governanceCockpit/GovernanceCockpit"));
const LogisticsPage = React.lazy(() => import("../modules/logistics/LogisticsPage"));
const ProcurementPage = React.lazy(() => import("../modules/procurement/ProcurementPage"));
const ProjectHub = React.lazy(() => import("../modules/projects/ProjectHub"));
const SimulationPage = React.lazy(() => import("../modules/simulation/SimulationPage"));
const SiteExecutionPage = React.lazy(() => import("../modules/chantier/SiteExecutionPage"));

function routeFallback() {
  return <div className="live-refresh">Chargement du module SP2I...</div>;
}

function suspense(page) {
  return <React.Suspense fallback={routeFallback()}>{page}</React.Suspense>;
}

const cockpitRoutes = {
  "/app/projects": null,
  "/app": suspense(<CockpitPage />),
  "/app/simulation": suspense(<SimulationPage />),
  "/app/approvisionnement": suspense(<ApprovisionnementDashboard />),
  "/app/procurement": suspense(<ProcurementPage />),
  "/app/procurement-intelligence": suspense(<ProcurementIntelligenceCockpit />),
  "/app/governance-cockpit": suspense(<GovernanceCockpit />),
  "/app/logistics": suspense(<LogisticsPage />),
  "/app/site": suspense(<SiteExecutionPage />),
  "/app/dqe": suspense(<DqePage />),
  "/app/analytics": suspense(<AnalyticsPage />),
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
    ? suspense(<SimulationPage defaultTab={searchParams.get("tab") || "simulation"} />)
    : routePath === "/app/projects"
      ? suspense(<ProjectHub onNavigate={navigateTo} />)
    : cockpitRoutes[routePath] || suspense(<CockpitPage />);

  return <AppShell activePath={path} onNavigate={navigateTo}>{page}</AppShell>;
}
