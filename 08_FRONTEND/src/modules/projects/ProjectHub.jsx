import React from "react";
import { Building2, FileSpreadsheet, Gauge, Plus, ShieldCheck, Users } from "lucide-react";
import { useAppStore } from "../../store/appStore.jsx";
import { getStoredSession } from "../../services/authService";
import { createProject, getProjectPrimaryAction, getProjectWorkflow, getProjectWorkspaceKey, listProjects } from "../../services/projectService";
import { formatMoney } from "../../shared/formatters";
import ProjectSetupWizard from "./ProjectSetupWizard";
import ProjectWorkflowStepper from "./ProjectWorkflowStepper";

const roleLabels = {
  ADMIN: "Administrateur",
  MANAGER: "Manager projet",
  ANALYST: "Analyste",
  VIEWER: "Lecture seule",
};

export default function ProjectHub({ onNavigate }) {
  const { state, setState } = useAppStore();
  const [session] = React.useState(() => getStoredSession());
  const [projects, setProjects] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [creating, setCreating] = React.useState(false);
  const [setupProject, setSetupProject] = React.useState(null);

  React.useEffect(() => {
    let mounted = true;
    listProjects()
      .then((payload) => {
        if (mounted) setProjects(payload.projects || []);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const openProject = (project) => {
    setState((current) => ({ ...current, activeProject: getProjectWorkspaceKey(project), activeProjectDetails: project }));
    onNavigate("/app");
  };

  const runPrimaryAction = (project) => {
    const action = getProjectPrimaryAction(project, state);
    setState((current) => ({ ...current, activeProject: getProjectWorkspaceKey(project), activeProjectDetails: project }));
    if (action.mode === "setup") {
      setSetupProject(project);
      return;
    }
    onNavigate(action.route);
  };

  const saveProjectSetup = (updatedProject) => {
    setProjects((current) => current.map((project) => project.id === updatedProject.id ? updatedProject : project));
    setState((current) => ({ ...current, activeProject: getProjectWorkspaceKey(updatedProject), activeProjectDetails: updatedProject }));
    setSetupProject(null);
  };

  const addProject = async () => {
    setCreating(true);
    try {
      const project = await createProject({
        name: "Nouveau projet CAPEX",
        client_name: "",
        city: "",
        country: "Congo-Brazzaville",
        currency: "FCFA",
      });
      setProjects((current) => [project, ...current]);
      setSetupProject(project);
    } finally {
      setCreating(false);
    }
  };

  return (
    <main className="project-hub-page">
      <section className="project-hub-hero">
        <div>
          <p className="eyebrow">Workspace de pilotage immobilier</p>
          <h1>Mes projets</h1>
          <p>Chaque projet isole son DQE, ses scenarios, ses arbitrages achats, ses indicateurs et sa gouvernance.</p>
        </div>
        <div className="project-hub-user">
          <Users size={18} />
          <span>{session?.user?.full_name || "Utilisateur SP2I"}</span>
          <strong>{roleLabels[session?.user?.role] || "Manager projet"}</strong>
        </div>
      </section>

      <section className="workspace-model-strip" aria-label="Modele workspace">
        {["Organisation", "Utilisateurs", "Projets", "DQE", "Scenarios", "Analytics", "Governance"].map((item) => (
          <span key={item}>{item}</span>
        ))}
      </section>

      <section className="project-hub-toolbar">
        <div>
          <strong>{projects.length || 0} workspace(s) projet</strong>
          <span>ADMIN, MANAGER, ANALYST et VIEWER structurent les permissions minimales.</span>
        </div>
        <button type="button" onClick={addProject} disabled={creating}>
          <Plus size={17} /> Nouveau projet
        </button>
      </section>

      <section className="project-card-grid" aria-live="polite">
        {loading ? <div className="project-card skeleton-project">Chargement des projets...</div> : null}
        {projects.map((project) => {
          const workflow = getProjectWorkflow(project, state);
          const primaryAction = getProjectPrimaryAction(project, state);
          return (
            <article className="project-card" key={project.id}>
              <div className="project-card-top">
                <span><Building2 size={16} /> {project.city || "Ville a renseigner"}, {project.country || "Pays a renseigner"}</span>
                <strong>{workflow.label}</strong>
              </div>
              <h2>{project.name}</h2>
              <p>{project.client_name || "Client / organisation a renseigner"}</p>
              <div className="project-card-metrics">
                <span><ShieldCheck size={15} /> Confiance {project.trust_score ?? 0}/100</span>
                <span><FileSpreadsheet size={15} /> Configuration {project.setup_completion_percent ?? workflow.completion}%</span>
                <span><FileSpreadsheet size={15} /> {project.last_dqe || "DQE a importer"}</span>
                <span><Gauge size={15} /> {project.budget ? formatMoney(project.budget) : "Budget a synchroniser"}</span>
              </div>
              <ProjectWorkflowStepper workflow={workflow} onNavigate={onNavigate} onSetup={() => setSetupProject(project)} />
              <div className="project-card-actions">
                <button type="button" onClick={() => runPrimaryAction(project)}>{primaryAction.label}</button>
                <button type="button" className="secondary" onClick={() => openProject(project)}>Ouvrir le workspace</button>
              </div>
            </article>
          );
        })}
      </section>
      {setupProject ? (
        <ProjectSetupWizard
          project={setupProject}
          onClose={() => setSetupProject(null)}
          onSave={saveProjectSetup}
          onImportDqe={() => onNavigate("/app/dqe?tab=import")}
        />
      ) : null}
    </main>
  );
}
