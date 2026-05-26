/**
 * workflowHelpers.js
 * 
 * Helpers pour manipuler les workflows d'orchestration.
 */

export async function getWorkflowState(page, workflowName) {
  /**
   * Récupère l'état complet d'un workflow.
   */
  return await page.evaluate(({ name }) => {
    const workflow = document.querySelector(`[data-testid="workflow-${name}"]`);
    if (!workflow) return null;

    return {
      name: workflow.dataset.name,
      status: workflow.dataset.status,
      priority: workflow.dataset.priority,
      blocked: workflow.dataset.blocked === 'true',
      blocker: workflow.dataset.blocker,
      eta: workflow.dataset.eta,
      actions: Array.from(
        workflow.querySelectorAll('[data-testid="action"]')
      ).map(a => ({
        id: a.dataset.actionId,
        title: a.textContent,
        status: a.dataset.status,
        priority: a.dataset.priority,
      })),
      responsibles: workflow.dataset.responsible?.split(',') || [],
    };
  }, { name: workflowName });
}

export async function updateWorkflowStatus(page, workflowName, newStatus) {
  /**
   * Met à jour le statut d'un workflow via l'API.
   */
  await page.evaluate(({ name, status }) => {
    window.dispatchEvent(new CustomEvent('orchestration:workflow-status-update', {
      detail: {
        workflow: name,
        newStatus: status,
        timestamp: new Date().toISOString(),
      }
    }));
  }, { name: workflowName, status: newStatus });

  await page.waitForTimeout(500);
}

export async function assignResponsible(page, workflowName, responsible) {
  /**
   * Assigne un responsable à un workflow.
   */
  await page.evaluate(({ name, resp }) => {
    window.dispatchEvent(new CustomEvent('orchestration:workflow-assign', {
      detail: {
        workflow: name,
        responsible: resp,
        timestamp: new Date().toISOString(),
      }
    }));
  }, { name: workflowName, resp: responsible });

  await page.waitForTimeout(500);
}

export async function getAllWorkflows(page) {
  /**
   * Récupère tous les workflows visibles.
   */
  return await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid^="workflow-"]')
    ).map(el => ({
      name: el.dataset.testid.replace('workflow-', ''),
      status: el.dataset.status,
      priority: el.dataset.priority,
      blocked: el.dataset.blocked === 'true',
    }));
  });
}

export async function getBlockedWorkflows(page) {
  /**
   * Retourne les workflows bloqués.
   */
  const all = await getAllWorkflows(page);
  return all.filter(w => w.blocked);
}

export async function getCriticalWorkflows(page) {
  /**
   * Retourne les workflows critiques.
   */
  const all = await getAllWorkflows(page);
  return all.filter(w => w.priority === 'CRITICAL');
}

export async function assertWorkflowStatus(page, workflowName, expectedStatus) {
  /**
   * Assertion : workflow a le statut attendu.
   */
  const state = await getWorkflowState(page, workflowName);
  if (!state) throw new Error(`Workflow ${workflowName} not found`);
  if (state.status !== expectedStatus) {
    throw new Error(`Workflow ${workflowName} status ${state.status} != ${expectedStatus}`);
  }
  return true;
}

export async function assertWorkflowNotBlocked(page, workflowName) {
  /**
   * Assertion : workflow n'est pas bloqué.
   */
  const state = await getWorkflowState(page, workflowName);
  if (state?.blocked) {
    throw new Error(`Workflow ${workflowName} ne devrait pas être bloqué`);
  }
  return true;
}

export async function assertWorkflowIsBlockedBy(page, blockedWorkflow, blockerWorkflow) {
  const state = await getWorkflowState(page, blockedWorkflow);
  if (!state?.blocked) {
    throw new Error(`Workflow ${blockedWorkflow} devrait être bloqué`);
  }
  if (blockerWorkflow && state.blocker && state.blocker !== blockerWorkflow) {
    throw new Error(`Workflow ${blockedWorkflow} bloqué par ${state.blocker}, attendu ${blockerWorkflow}`);
  }
  return true;
}

export async function assertResponsibleAssigned(page, workflowName, responsible) {
  /**
   * Assertion : responsable assigné au workflow.
   */
  const state = await getWorkflowState(page, workflowName);
  if (!state?.responsibles.includes(responsible)) {
    throw new Error(`Responsable ${responsible} pas assigné à ${workflowName}`);
  }
  return true;
}
