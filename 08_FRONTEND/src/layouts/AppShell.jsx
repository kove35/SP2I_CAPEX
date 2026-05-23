import React from "react";
import { AlertTriangle, Gauge, Menu } from "lucide-react";
import Sidebar from "../components/layout/sidebar/Sidebar";
import { useSidebarStore } from "../components/layout/sidebar/sidebarStore";
import { useAppStore } from "../store/appStore.jsx";
import { getScenarioContext } from "../utils/businessContext";
import AlertCenter from "../ui/AlertCenter";
import ProjectSelector from "../ui/ProjectSelector";
import ProjectQuickActions from "../components/ProjectQuickActions";
import ProjectWorkflowBreadcrumb, { moduleFromPath } from "../modules/projects/ProjectWorkflowBreadcrumb";
import { getBackendProjectWorkflow, getProjectWorkflow } from "../services/projectService";

export default function AppShell({ activePath, onNavigate, children }) {
  const { state, setState } = useAppStore();
  const { isCollapsed, toggleMobile, setProjectContext } = useSidebarStore();
  const scenario = getScenarioContext(state.activeScenario);
  const workflow = React.useMemo(
    () => getProjectWorkflow(state.activeProjectDetails || { id: state.activeProject, workspace_key: state.activeProject }, state),
    [state]
  );
  const showWorkspaceWorkflow = !["/app", "/app/"].includes(String(activePath || "")) && !String(activePath || "").startsWith("/app/projects");

  React.useEffect(() => {
    setProjectContext({
      project: state.activeProject,
      scenario: state.activeScenario,
    });
  }, [setProjectContext, state.activeProject, state.activeScenario]);

  React.useEffect(() => {
    const project = state.activeProjectDetails || { id: state.activeProject, workspace_key: state.activeProject };
    const projectId = project?.id;
    if (!projectId || project.backendWorkflow || project.backend_workflow) return;

    let mounted = true;
    getBackendProjectWorkflow(projectId).then((backendWorkflow) => {
      if (!mounted || !backendWorkflow) return;
      setState((current) => {
        if (!current.activeProjectDetails || String(current.activeProjectDetails.id) !== String(projectId)) {
          return current;
        }
        return {
          ...current,
          activeProjectDetails: {
            ...current.activeProjectDetails,
            backendWorkflow,
          },
        };
      });
    });
    return () => {
      mounted = false;
    };
  }, [state.activeProject, state.activeProjectDetails, setState]);

  return (
    <div className={`saas-shell ${isCollapsed ? "is-collapsed" : ""}`}>
      <Sidebar activePath={activePath} onNavigate={onNavigate} />
      <div className="saas-main">
        <header className="topbar" data-testid="workspace-header">
          <button className="icon-button mobile-menu" type="button" onClick={toggleMobile} title="Menu">
            <Menu size={18} />
          </button>
          <ProjectSelector />
          <div className="topbar-metrics">
            <span><Gauge size={16} /> Strategie : {scenario.label}</span>
            <span><AlertTriangle size={16} /> Risque global moyen</span>
          </div>
          <ProjectQuickActions onNavigate={onNavigate} />
          <AlertCenter />
        </header>
        <section className="content-area">
          {showWorkspaceWorkflow ? (
            <ProjectWorkflowBreadcrumb
              workflow={workflow}
              currentModule={moduleFromPath(activePath)}
              showAction
              onNavigate={onNavigate}
              onSetup={() => onNavigate("/app/projects")}
            />
          ) : null}
          {children}
        </section>
      </div>
    </div>
  );
}
