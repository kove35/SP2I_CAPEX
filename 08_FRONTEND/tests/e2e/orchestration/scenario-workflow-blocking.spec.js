/**
 * scenario-workflow-blocking.spec.js
 * 
 * Test d'orchestration : blocage de workflow
 * Scénario: Menuiserie bloquée → peinture bloquée automatiquement
 * 
 * Cela valide:
 * - Détection dépendance workflow
 * - Blocage propagation
 * - Actions d'escalade générées
 * - Réconciliation timeline
 */

import { test, expect } from "@playwright/test";
import {
  blockWorkflow,
  getWorkflowStatus,
  waitForWorkflowUpdate,
} from "../helpers/orchestrationHelpers";
import {
  getWorkflowState,
  getBlockedWorkflows,
  assertWorkflowIsBlockedBy,
} from "../helpers/workflowHelpers";
import {
  getEventFeedFull,
  waitForEventType,
  getEventChain,
} from "../helpers/eventHelpers";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { WORKFLOW_BLOCKING_SCENARIO } from "../fixtures/orchestration-scenarios.mock";

test.describe("Orchestration: Workflow Blocking", () => {
  
  test.beforeEach(async ({ page }) => {
    const workflowsOverride = {
      workflows: [
        {
          id: 'wf_menuiserie',
          name: 'menuiserie',
          status: 'IN_PROGRESS',
          priority: 'HIGH',
          blocked: false,
          actions: [],
        },
        {
          id: 'wf_peinture',
          name: 'peinture',
          status: 'TO_DO',
          priority: 'HIGH',
          blocked: false,
          actions: [],
        },
      ],
    };
    
    await mockAllApisForSpatialExecution(page, workflowsOverride);
    
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should detect source workflow blocker", async ({ page }) => {
    /**
     * Étape 1: Vérifier l'état initial
     * - Menuiserie: IN_PROGRESS
     * - Peinture: TO_DO
     */
    let menuiserieWf = await getWorkflowState(page, 'menuiserie');
    expect(menuiserieWf.status).toBe('IN_PROGRESS');
    expect(menuiserieWf.blocked).toBe(false);

    let peintureWf = await getWorkflowState(page, 'peinture');
    expect(peintureWf.blocked).toBe(false);
  });

  test("should block workflow on component unavailable", async ({ page }) => {
    /**
     * Étape 2: Bloquer menuiserie (composant indisponible)
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 3: Vérifier que menuiserie passe à BLOCKED
     */
    let menuiserieWf = await getWorkflowState(page, 'menuiserie');
    expect(menuiserieWf.status).toBe('BLOCKED');
    expect(menuiserieWf.blocked).toBe(true);
  });

  test("should propagate blocking to dependent workflow", async ({ page }) => {
    /**
     * Étape 4: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 5: Vérifier que peinture devient aussi bloquée
     * car elle dépend de menuiserie
     */
    let peintureWf = await getWorkflowState(page, 'peinture');
    expect(peintureWf.blocked).toBe(true);
    expect(peintureWf.blocker).toContain('menuiserie');
  });

  test("should generate WORKFLOW_BLOCKING event", async ({ page }) => {
    /**
     * Étape 6: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 7: Vérifier événement WORKFLOW_BLOCKING_STARTED
     */
    const blockingEvent = await waitForEventType(page, 'WORKFLOW_BLOCKING_STARTED', 5000);
    expect(blockingEvent).toBeDefined();
    expect(blockingEvent.workflow).toBe('menuiserie');
    expect(blockingEvent.severity).toBe('CRITICAL');
  });

  test("should generate DEPENDENT_WORKFLOW_BLOCKED event", async ({ page }) => {
    /**
     * Étape 8: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 9: Vérifier événement DEPENDENT_WORKFLOW_BLOCKED pour peinture
     */
    const depEvent = await waitForEventType(page, 'DEPENDENT_WORKFLOW_BLOCKED', 5000);
    expect(depEvent).toBeDefined();
    expect(depEvent.workflow).toBe('peinture');
    expect(depEvent.dependsOn).toBe('menuiserie');
  });

  test("should generate resolution actions", async ({ page }) => {
    /**
     * Étape 10: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 11: Vérifier que des actions RESOLVE_BLOCKER sont générées
     */
    const actions = await page.evaluate(() => {
      return Array.from(
        document.querySelectorAll('[data-testid="action"][data-action-type="RESOLVE_BLOCKER"]')
      ).map(el => ({
        title: el.textContent,
        priority: el.dataset.priority,
        workflow: el.dataset.workflow,
      }));
    });

    expect(actions.length).toBeGreaterThanOrEqual(1);
    expect(actions.some(a => a.priority === 'CRITICAL')).toBe(true);
  });

  test("should have escalation for dependent workflows", async ({ page }) => {
    /**
     * Étape 12: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 13: Vérifier qu'une action WAIT_FOR_DEPENDENCY existe pour peinture
     */
    const waitActions = await page.evaluate(() => {
      return Array.from(
        document.querySelectorAll('[data-testid="action"][data-action-type="WAIT_FOR_DEPENDENCY"]')
      ).map(el => ({
        title: el.textContent,
        priority: el.dataset.priority,
      }));
    });

    expect(waitActions.length).toBeGreaterThan(0);
    expect(waitActions[0].priority).toBe('HIGH');
  });

  test("should track complete blocking chain", async ({ page }) => {
    /**
     * Étape 14: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 15: Vérifier la chaîne d'événements complète
     */
    const chain = await getEventChain(
      page,
      'WORKFLOW_BLOCKING_STARTED',
      'DEPENDENT_WORKFLOW_BLOCKED',
      5
    );

    expect(chain.found).toBe(true);
    expect(chain.distance).toBe(2);  // Au moins 2 hops
  });

  test("should be reversible (unblock workflow)", async ({ page }) => {
    /**
     * Étape 16: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 17: Vérifier l'état bloqué
     */
    let menuiserieWf = await getWorkflowState(page, 'menuiserie');
    expect(menuiserieWf.blocked).toBe(true);

    /**
     * Étape 18: Débloquer menuiserie
     */
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('orchestration:workflow-unblock', {
        detail: {
          workflow: 'menuiserie',
          reason: 'BLOCKER_RESOLVED',
        }
      }));
    });
    await page.waitForTimeout(500);

    /**
     * Étape 19: Vérifier que menuiserie n'est plus bloquée
     */
    menuiserieWf = await getWorkflowState(page, 'menuiserie');
    expect(menuiserieWf.blocked).toBe(false);

    /**
     * Étape 20: Vérifier que peinture n'est plus bloquée non plus
     */
    let peintureWf = await getWorkflowState(page, 'peinture');
    expect(peintureWf.blocked).toBe(false);
  });

  test("should get list of all blocked workflows", async ({ page }) => {
    /**
     * Étape 21: État initial - aucun workflow bloqué
     */
    let blockedWfs = await getBlockedWorkflows(page);
    expect(blockedWfs.length).toBe(0);

    /**
     * Étape 22: Bloquer menuiserie
     */
    await blockWorkflow(page, 'menuiserie_component_unavailable');
    await page.waitForTimeout(500);

    /**
     * Étape 23: Vérifier que 2 workflows sont bloqués
     */
    blockedWfs = await getBlockedWorkflows(page);
    expect(blockedWfs.length).toBe(2);  // menuiserie + peinture
    expect(blockedWfs.map(w => w.name)).toContain('menuiserie');
    expect(blockedWfs.map(w => w.name)).toContain('peinture');
  });

  test("should maintain temporal consistency", async ({ page }) => {
    /**
     * Étape 24: Bloquer menuiserie à t0
     */
    const t0 = Date.now();
    await blockWorkflow(page, 'menuiserie_component_unavailable');

    /**
     * Étape 25: Attendre que peinture soit bloquée (should be quasi-immédiat)
     */
    const blockingEvent = await waitForEventType(page, 'DEPENDENT_WORKFLOW_BLOCKED', 5000);
    const blockingTime = Date.now() - t0;

    /**
     * Étape 26: Vérifier que la propagation était rapide (< 1000ms)
     */
    expect(blockingTime).toBeLessThan(1000);
  });
});
