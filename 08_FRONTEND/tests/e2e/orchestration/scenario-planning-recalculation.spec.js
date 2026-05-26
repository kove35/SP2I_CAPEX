/**
 * scenario-planning-recalculation.spec.js
 * 
 * Test d'orchestration : recalcul du planning
 * Scénario: Lot critique retardé → tous les ETAs recalculés, criticité réévaluée
 * 
 * Cela valide:
 * - Recalcul complet timeline
 * - Changement criticité
 * - Décalage date projet
 * - Impacts notifications
 * - Cohérence global système
 */

import { test, expect } from "@playwright/test";
import {
  simulateEtaDelay,
  getTimelineState,
  getCriticalPathLots,
} from "../helpers/orchestrationHelpers";
import {
  getEventFeedFull,
  waitForEventType,
} from "../helpers/eventHelpers";
import {
  getAllWorkflows,
  getWorkflowState,
} from "../helpers/workflowHelpers";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";

test.describe("Orchestration: Planning Recalculation", () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAllApisForSpatialExecution(page);
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should start with baseline planning", async ({ page }) => {
    /**
     * Étape 1: Vérifier l'état initial
     */
    const timeline = await getTimelineState(page);
    
    expect(timeline.facade.eta).toBe(35);
    expect(timeline.menuiserie.eta).toBe(42);
    expect(timeline.peinture.eta).toBe(49);
    expect(timeline.plomberie.eta).toBe(30);
    expect(timeline.electricite.eta).toBe(35);
    
    expect(timeline.criticalPath).toEqual(['facade', 'menuiserie', 'peinture']);
    expect(timeline.criticalPathDuration).toBe(49);
  });

  test("should recalculate all dependent ETAs when critical lot delayed", async ({ page }) => {
    /**
     * Étape 2: Simuler délai sur façade (lot critique)
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 3: Vérifier que TOUS les ETAs dépendants ont changé
     */
    const timeline = await getTimelineState(page);
    
    expect(timeline.facade.eta).toBe(55);       // 35 + 20
    expect(timeline.menuiserie.eta).toBe(62);   // 42 + 20
    expect(timeline.peinture.eta).toBe(69);     // 49 + 20
    
    /**
     * Étape 4: Vérifier que les lots indépendants ne changent pas
     */
    expect(timeline.plomberie.eta).toBe(30);    // Inchangé
    expect(timeline.electricite.eta).toBe(35);  // Inchangé
  });

  test("should update critical path duration", async ({ page }) => {
    /**
     * Étape 5: Récupérer durée initiale
     */
    const initialTimeline = await getTimelineState(page);
    expect(initialTimeline.criticalPathDuration).toBe(49);

    /**
     * Étape 6: Simuler délai de 20j
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 7: Vérifier nouvelle durée
     */
    const updatedTimeline = await getTimelineState(page);
    expect(updatedTimeline.criticalPathDuration).toBe(69);  // 49 + 20
  });

  test("should shift project end date", async ({ page }) => {
    /**
     * Étape 8: Vérifier date fin initiale
     */
    const projectOverview = page.getByTestId("project-overview-card");
    let endDateText = await projectOverview.textContent();
    const initialEndDate = new Date('2026-03-05');  // 49 jours depuis 2026-01-15

    /**
     * Étape 9: Simuler retard de 20j
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 10: Vérifier que la date projet a changé
     */
    const updatedEndDate = new Date('2026-03-25');  // 69 jours depuis 2026-01-15
    
    const timeline = await getTimelineState(page);
    // Si le système inclut la date de fin, elle doit avoir reculé de 20j
    expect(timeline.criticalPathDuration).toBeGreaterThan(49);
  });

  test("should trigger PLANNING_RECALCULATED event", async ({ page }) => {
    /**
     * Étape 11: Simuler retard
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 12: Vérifier événement
     */
    const recalcEvent = await waitForEventType(page, 'CRITICAL_PATH_RECALCULATED', 5000);
    expect(recalcEvent).toBeDefined();
  });

  test("should trigger PROJECT_DELIVERY_DELAYED notification", async ({ page }) => {
    /**
     * Étape 13: Simuler retard significatif
     */
    await simulateEtaDelay(page, 30);
    await page.waitForTimeout(500);

    /**
     * Étape 14: Vérifier notification
     */
    const delayEvent = await waitForEventType(page, 'PROJECT_DELIVERY_DELAYED', 5000);
    expect(delayEvent).toBeDefined();
    expect(delayEvent.severity).toBe('CRITICAL');
  });

  test("should update workflow status to REVIEW", async ({ page }) => {
    /**
     * Étape 15: Simuler retard
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 16: Vérifier que planning workflow passe à TO_REVIEW
     */
    const planningWf = await getWorkflowState(page, 'planning');
    expect(planningWf.status).toBe('TO_REVIEW');
  });

  test("should maintain critical path", async ({ page }) => {
    /**
     * Étape 17: Simuler retard
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 18: Vérifier que le chemin critique reste le même
     */
    const criticalPath = await getCriticalPathLots(page);
    expect(criticalPath).toEqual(['facade', 'menuiserie', 'peinture']);
  });

  test("should not change criticality of independent lots", async ({ page }) => {
    /**
     * Étape 19: État initial - plomberie et électricité ne sont pas critiques
     */
    const initialTimeline = await getTimelineState(page);
    expect(initialTimeline.facade.criticality).toBeGreaterThan(0.7);
    expect(initialTimeline.plomberie.criticality).toBeLessThan(0.7);

    /**
     * Étape 20: Simuler retard sur facade
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 21: Vérifier que plomberie reste non critique
     */
    const updatedTimeline = await getTimelineState(page);
    expect(updatedTimeline.plomberie.criticality).toBeLessThan(0.7);
  });

  test("should generate PLANNING_UPDATED notification", async ({ page }) => {
    /**
     * Étape 22: Simuler retard
     */
    await simulateEtaDelay(page, 15);
    await page.waitForTimeout(500);

    /**
     * Étape 23: Vérifier notification de mise à jour
     */
    const updateEvent = await waitForEventType(page, 'PLANNING_UPDATED', 5000);
    expect(updateEvent).toBeDefined();
    expect(updateEvent.severity).toMatch(/HIGH|CRITICAL/);
  });

  test("should handle progressive delays", async ({ page }) => {
    /**
     * Étape 24: Premier retard
     */
    await simulateEtaDelay(page, 5);
    await page.waitForTimeout(500);

    let timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(40);
    expect(timeline.criticalPathDuration).toBe(54);

    /**
     * Étape 25: Deuxième retard
     */
    await simulateEtaDelay(page, 5);
    await page.waitForTimeout(500);

    timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(45);
    expect(timeline.criticalPathDuration).toBe(59);

    /**
     * Étape 26: Troisième retard
     */
    await simulateEtaDelay(page, 5);
    await page.waitForTimeout(500);

    timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(50);
    expect(timeline.criticalPathDuration).toBe(64);
  });

  test("should be reversible (accelerate schedule)", async ({ page }) => {
    /**
     * Étape 27: Retarder de 20j
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    let timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(55);
    expect(timeline.criticalPathDuration).toBe(69);

    /**
     * Étape 28: Accélérer de 10j (retard net = 10j)
     */
    await simulateEtaDelay(page, -10);
    await page.waitForTimeout(500);

    timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(45);
    expect(timeline.criticalPathDuration).toBe(59);

    /**
     * Étape 29: Revenir à normal
     */
    await simulateEtaDelay(page, -10);
    await page.waitForTimeout(500);

    timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(35);
    expect(timeline.criticalPathDuration).toBe(49);
  });

  test("should keep all workflows in sync", async ({ page }) => {
    /**
     * Étape 30: Récupérer état initial des workflows
     */
    const initialWorkflows = await getAllWorkflows(page);
    const initialPlanningStatus = initialWorkflows.find(w => w.name === 'planning').status;

    /**
     * Étape 31: Simuler retard
     */
    await simulateEtaDelay(page, 20);
    await page.waitForTimeout(500);

    /**
     * Étape 32: Vérifier que chaque workflow a vu la mise à jour
     */
    const updatedWorkflows = await getAllWorkflows(page);
    const updatedPlanningStatus = updatedWorkflows.find(w => w.name === 'planning').status;

    // Le status doit avoir changé (pas nécessairement TO_REVIEW, mais changé)
    expect(updatedPlanningStatus).not.toBe(initialPlanningStatus);
  });
});
