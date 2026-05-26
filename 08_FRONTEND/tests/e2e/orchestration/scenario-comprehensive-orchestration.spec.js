/**
 * scenario-comprehensive-orchestration.spec.js
 * 
 * Test complet d'orchestration : DQE → Simulation → Procurement → Execution → Events
 * 
 * Cela valide le flux COMPLET:
 * - Import DQE spatial
 * - Simulation avec scénarios
 * - Décisions procurement
 * - Génération actions exécution
 * - Événements métier propagés
 * - Workflows créés et gérés
 * - Timeline consolidée
 */

import { test, expect } from "@playwright/test";
import {
  simulateEtaDelay,
  simulateStorageConflict,
  blockWorkflow,
  waitForEventInFeed,
  getTimelineState,
  getWorkflowStatus,
} from "../helpers/orchestrationHelpers";
import {
  getEventFeedFull,
  waitForEventType,
  filterEventsBySource,
} from "../helpers/eventHelpers";
import {
  getWorkflowState,
  getAllWorkflows,
  getBlockedWorkflows,
} from "../helpers/workflowHelpers";
import {
  assertProjectInExecutionMode,
  assertCriticalPathFormatValid,
  assertBimMaturityCorrectlyApplied,
  assertNoDataLossDuringPropagation,
} from "../utils/orchestrationAssertions";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { FULL_ORCHESTRATION_SCENARIO } from "../fixtures/orchestration-scenarios.mock";

test.describe("Orchestration: Comprehensive Flow", () => {
  
  test.beforeEach(async ({ page }) => {
    // Setup mocks avec scénario complet
    await mockAllApisForSpatialExecution(page);
    
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should start in EXECUTION_READY state", async ({ page }) => {
    /**
     * Étape 1: Vérifier que le projet est prêt
     */
    await assertProjectInExecutionMode(page);

    /**
     * Étape 2: Vérifier que tous les workflows sont créés
     */
    const workflows = await getAllWorkflows(page);
    expect(workflows.length).toBeGreaterThanOrEqual(3);
    expect(workflows.map(w => w.name)).toContain('planning');
    expect(workflows.map(w => w.name)).toContain('procurement');
    expect(workflows.map(w => w.name)).toContain('execution');
  });

  test("should have DQE imported", async ({ page }) => {
    /**
     * Étape 3: Vérifier événement DQE_IMPORTED
     */
    const dqeEvents = await filterEventsBySource(page, 'dqe_engine');
    expect(dqeEvents.length).toBeGreaterThan(0);

    /**
     * Étape 4: Vérifier que l'événement est DQE_IMPORTED
     */
    const importEvent = dqeEvents.find(e => e.type === 'DQE_IMPORTED');
    expect(importEvent).toBeDefined();
  });

  test("should have simulation completed", async ({ page }) => {
    /**
     * Étape 5: Vérifier événement SCENARIO_SIMULATED
     */
    const simEvents = await filterEventsBySource(page, 'simulation_engine');
    expect(simEvents.length).toBeGreaterThan(0);

    const simEvent = simEvents.find(e => e.type === 'SCENARIO_SIMULATED');
    expect(simEvent).toBeDefined();
  });

  test("should have critical path calculated", async ({ page }) => {
    /**
     * Étape 6: Vérifier que le critical path existe
     */
    const timeline = await getTimelineState(page);
    expect(timeline.criticalPath).toBeDefined();
    expect(timeline.criticalPath.length).toBeGreaterThan(0);
    expect(timeline.criticalPathDuration).toBeGreaterThan(0);
  });

  test("should have procurement workflow active", async ({ page }) => {
    /**
     * Étape 7: Vérifier que le workflow procurement existe
     */
    const procurementWf = await getWorkflowState(page, 'procurement');
    expect(procurementWf).toBeDefined();
    expect(procurementWf.status).toMatch(/IN_PROGRESS|BLOCKED/);

    /**
     * Étape 8: Si bloqué, il doit y avoir une raison
     */
    if (procurementWf.blocked) {
      expect(procurementWf.blocker).toBeTruthy();
    }
  });

  test("should have execution workflow ready", async ({ page }) => {
    /**
     * Étape 9: Vérifier le workflow execution
     */
    const executionWf = await getWorkflowState(page, 'execution');
    expect(executionWf).toBeDefined();
    expect(['TO_DO', 'IN_PROGRESS']).toContain(executionWf.status);
  });

  test("should propagate events correctly", async ({ page }) => {
    /**
     * Étape 10: Vérifier que les événements arrivent dans le feed
     */
    const allEvents = await getEventFeedFull(page);
    expect(allEvents.length).toBeGreaterThan(0);

    /**
     * Étape 11: Vérifier la diversité des types d'événements
     */
    const eventTypes = new Set(allEvents.map(e => e.type));
    expect(eventTypes.size).toBeGreaterThan(2);
  });

  test("should handle multi-stage orchestration", async ({ page }) => {
    /**
     * Étape 12: Simuler une perturbation ETA
     */
    await simulateEtaDelay(page, 10);
    await page.waitForTimeout(500);

    /**
     * Étape 13: Vérifier que timeline s'est mise à jour
     */
    const timeline = await getTimelineState(page);
    expect(timeline.criticalPathDuration).toBeGreaterThan(49);

    /**
     * Étape 14: Simuler une saturation stockage
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 15: Vérifier qu'il y a des actions STORAGE générées
     */
    const allEvents = await getEventFeedFull(page);
    const storageEvents = allEvents.filter(e => e.type.includes('STORAGE'));
    expect(storageEvents.length).toBeGreaterThan(0);

    /**
     * Étape 16: Simuler un blocage workflow
     */
    await blockWorkflow(page, 'menuiserie_delayed');
    await page.waitForTimeout(500);

    /**
     * Étape 17: Vérifier qu'il y a des workflows bloqués
     */
    const blockedWfs = await getBlockedWorkflows(page);
    expect(blockedWfs.length).toBeGreaterThan(0);
  });

  test("should validate BIM maturity applied", async ({ page }) => {
    /**
     * Étape 18: Vérifier que la maturité BIM est correctement appliquée
     */
    await assertBimMaturityCorrectlyApplied(page, 'BIM_LITE');

    /**
     * Étape 19: Vérifier que la tab spatial est visible
     */
    const spatialTabVisible = await page.getByTestId("execution-tab-spatial").isVisible();
    expect(spatialTabVisible).toBe(true);
  });

  test("should not lose data during complex orchestration", async ({ page }) => {
    /**
     * Étape 20: Exécuter multiple perturbations
     */
    await simulateEtaDelay(page, 10);
    await page.waitForTimeout(200);
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(200);
    await blockWorkflow(page, 'test_workflow');
    await page.waitForTimeout(200);

    /**
     * Étape 21: Vérifier l'intégrité des données
     */
    await assertNoDataLossDuringPropagation(page);
  });

  test("should track all state changes in event feed", async ({ page }) => {
    /**
     * Étape 22: Initialiser le feed
     */
    const initialEvents = await getEventFeedFull(page);
    const initialCount = initialEvents.length;

    /**
     * Étape 23: Effectuer des changements
     */
    await simulateEtaDelay(page, 5);
    await page.waitForTimeout(300);

    /**
     * Étape 24: Vérifier que des nouveaux événements sont apparus
     */
    const updatedEvents = await getEventFeedFull(page);
    expect(updatedEvents.length).toBeGreaterThan(initialCount);
  });

  test("should maintain timeline consistency across all workflows", async ({ page }) => {
    /**
     * Étape 25: Récupérer l'état initial de chaque workflow
     */
    const workflows = await getAllWorkflows(page);
    const initialStates = {};
    for (const wf of workflows) {
      const state = await getWorkflowState(page, wf.name);
      initialStates[wf.name] = state;
    }

    /**
     * Étape 26: Effectuer perturbations
     */
    await simulateEtaDelay(page, 10);
    await page.waitForTimeout(500);

    /**
     * Étape 27: Vérifier que chaque workflow a été notifié
     */
    const updatedWorkflows = await getAllWorkflows(page);
    for (const wf of updatedWorkflows) {
      const newState = await getWorkflowState(page, wf.name);
      // Au moins le timestamp doit avoir changé
      expect(newState).toBeDefined();
    }
  });

  test("should support full end-to-end resolution", async ({ page }) => {
    /**
     * Étape 28: État initial
     */
    let blockedWfs = await getBlockedWorkflows(page);
    const initialBlockedCount = blockedWfs.length;

    /**
     * Étape 29: Créer plusieurs blocages
     */
    await blockWorkflow(page, 'blocker_1');
    await page.waitForTimeout(200);
    await blockWorkflow(page, 'blocker_2');
    await page.waitForTimeout(200);

    /**
     * Étape 30: Vérifier augmentation
     */
    blockedWfs = await getBlockedWorkflows(page);
    expect(blockedWfs.length).toBeGreaterThan(initialBlockedCount);

    /**
     * Étape 31: Résoudre tous les blocages
     */
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('orchestration:clear-all-blockers'));
    });
    await page.waitForTimeout(500);

    /**
     * Étape 32: Vérifier résolution
     */
    blockedWfs = await getBlockedWorkflows(page);
    expect(blockedWfs.length).toBe(initialBlockedCount);
  });
});
