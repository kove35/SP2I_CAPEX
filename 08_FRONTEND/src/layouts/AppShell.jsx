import React from "react";
import { AlertTriangle, BarChart3, ChevronLeft, ChevronRight, FileSpreadsheet, Gauge, Menu, Play } from "lucide-react";
import { sidebarSections } from "../navigation/sidebarConfig";
import { useAppStore } from "../store/appStore.jsx";
import AlertCenter from "../ui/AlertCenter";
import ProjectSelector from "../ui/ProjectSelector";

export default function AppShell({ activePath, onNavigate, children }) {
  const [collapsed, setCollapsed] = React.useState(false);
  const { state } = useAppStore();
  const activeRoute = activePath.split("?")[0];

  const isActive = (itemPath) => {
    const itemRoute = itemPath.split("?")[0];
    if (itemPath === activePath) return true;
    return itemRoute === activeRoute && !activePath.includes("?") && itemPath === itemRoute;
  };

  return (
    <div className={`saas-shell ${collapsed ? "is-collapsed" : ""}`}>
      <aside className="saas-sidebar">
        <div className="brand-block">
          <button className="icon-button mobile-menu" type="button" onClick={() => setCollapsed(!collapsed)} title="Menu">
            <Menu size={18} />
          </button>
          <div>
            <strong>SP2I</strong>
            <span>CAPEX Control Tower</span>
          </div>
          <button className="icon-button collapse-button" type="button" onClick={() => setCollapsed(!collapsed)} title="Replier">
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {sidebarSections.map((section) => (
            <section key={section.title}>
              <p>{section.title}</p>
              {section.items.map((item) => {
                const Icon = item.icon;
                const active = activePath === item.path || (item.path !== "/app" && activePath.startsWith(item.path));
                return (
                  <button
                    type="button"
                    key={`${section.title}-${item.label}`}
                    className={isActive(item.path) || active ? "active" : ""}
                    onClick={() => onNavigate(item.path)}
                    title={item.label}
                  >
                    <Icon size={17} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </section>
          ))}
        </nav>
      </aside>

      <div className="saas-main">
        <header className="topbar">
          <ProjectSelector />
          <div className="topbar-metrics">
            <span><Gauge size={16} /> Scenario : {state.activeScenario}</span>
            <span><AlertTriangle size={16} /> Risque global moyen</span>
            <button type="button" onClick={() => onNavigate("/app/dqe?tab=import")}><FileSpreadsheet size={16} /> Importer DQE</button>
            <button type="button" onClick={() => onNavigate("/app/simulation")}><Play size={16} /> Simulation</button>
            <button type="button" onClick={() => onNavigate("/app/analytics?dashboard=direction")}><BarChart3 size={16} /> Power BI</button>
          </div>
          <AlertCenter />
        </header>
        <section className="content-area">{children}</section>
      </div>
    </div>
  );
}
