import React from "react";
import { getBackendProjectWorkflow, getBackendProjectWorkflowState, getProjectWorkflow } from "../services/projectService";
import { useAppStore } from "../store/appStore.jsx";

export function useWorkflow(projectId, projectOverride = null) {
  const { state, setState } = useAppStore();
  const project = projectOverride || state.activeProjectDetails || { id: projectId || state.activeProject, workspace_key: projectId || state.activeProject };
  const [backendWorkflow, setBackendWorkflow] = React.useState(Array.isArray(project?.backendWorkflow?.steps) ? project.backendWorkflow : Array.isArray(project?.backend_workflow?.steps) ? project.backend_workflow : null);
  const [backendWorkflowState, setBackendWorkflowState] = React.useState(project?.backendWorkflowState || project?.backend_workflow_state || null);

  React.useEffect(() => {
    const id = projectId || project?.id;
    if (!id || String(id).startsWith("local-")) return undefined;
    let mounted = true;

    Promise.all([
      getBackendProjectWorkflow(id),
      getBackendProjectWorkflowState(id),
    ]).then(([workflow, workflowState]) => {
      if (!mounted) return;

      if (workflow && Array.isArray(workflow.steps)) {
        setBackendWorkflow(workflow);
      }

      if (workflowState) {
        setBackendWorkflowState(workflowState);
      }

      setState((current) => {
        const currentProject = current.activeProjectDetails;
        if (!currentProject || String(currentProject.id) !== String(id)) return current;
        return {
          ...current,
          activeProjectDetails: {
            ...currentProject,
            ...(workflow && Array.isArray(workflow.steps) ? { backendWorkflow: workflow, backend_workflow: workflow } : {}),
            ...(workflowState ? { backendWorkflowState: workflowState, backend_workflow_state: workflowState } : {}),
          },
        };
      });
    });

    return () => {
      mounted = false;
    };
  }, [projectId, project?.id, setState]);

  const fallbackWorkflow = React.useMemo(() => getProjectWorkflow(project, state), [project, state]);
  const workflow = React.useMemo(() => backendWorkflow || fallbackWorkflow, [backendWorkflow, fallbackWorkflow]);

  return {
    workflow,
    workflowState: backendWorkflowState,
    isBackendDriven: Boolean(backendWorkflow || backendWorkflowState),
  };
}
