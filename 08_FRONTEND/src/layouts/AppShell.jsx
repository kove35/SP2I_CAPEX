import React from "react";
import { AlertTriangle, BarChart3, FileSpreadsheet, Gauge, Menu, Play } from "lucide-react";
import Sidebar from "../components/layout/sidebar/Sidebar";
import { useSidebarStore } from "../components/layout/sidebar/sidebarStore";
import { useAppStore } from "../store/appStore.jsx";
import AlertCenter from "../ui/AlertCenter";
import ProjectSelector from "../ui/ProjectSelector";

export default function AppShell({ activePath, onNavigate, children }) {
  const { state } = useAppStore();
  const { isCollapsed, toggleMobile, setProjectContext } = useSidebarStore();

  React.useEffect(() => {
    setProjectContext({
      project: state.activeProject,
      scenario: state.activeScenario,
    });
  }, [setProjectContext, state.activeProject, state.activeScenario]);

  return (
    <div className={`saas-shell ${isCollapsed ? "is-collapsed" : ""}`}>
      <Sidebar activePath={activePath} onNavigate={onNavigate} />
      <div className="saas-main">
        <header className="topbar">
          <button className="icon-button mobile-menu" type="button" onClick={toggleMobile} title="Menu">
            <Menu size={18} />
          </button>
          <ProjectSelector />
          <div className="topbar-metrics">
            <span><Gauge size={16} /> Scenario : {state.activeScenario}</span>
            <span><AlertTriangle size={16} /> Risque global moyen</span>
            <button type="button" onClick={() => onNavigate("/app/dqe?tab=import")}><FileSpreadsheet size={16} /> Importer DQE</button>
            <button type="button" onClick={() => onNavigate("/app/simulation")}><Play size={16} /> Simulation</button>
            <button type="button" onClick={() => onNavigate("/app/analytics?dashboard=direction")}><BarChart3 size={16} /> Analytics</button>
          </div>
          <AlertCenter />
        </header>
        <section className="content-area">{children}</section>
      </div>
    </div>
  );
}
