/**
 * scenario-delay-propagation.spec.js
 * 
 * Test d'orchestration : propagation de délai ETA
 * Scénario: ETA façade passe de 35 à 48 jours
 * Impact: Timeline complète se recalcule, menuiserie et peinture repoussées
 * 
 * Cela ne teste PAS juste du texte visible, mais:
 * - Événement ETA_DELAY générés
 * - Critical path recalculé
 * - Dépendances réajustées
 * - Workflows impactés
 * - Event feed mis à jour
 */

import { test, expect } from "@playwright/test";
import {
  simulateEtaDelay,
  waitForEventInFeed,
  getTimelineState,
  getCriticalPathLots,
  assertCriticalPathContains,
  assertPropagationChain,
} from "../helpers/orchestrationHelpers";
import {
  getCriticalPathSpatial,
  assertCriticalPathContainsSpatial,
} from "../helpers/spatialHelpers";
import {
  getEventFeedFull,
  waitForEventType,
  assertEventPropagation,
} from "../helpers/eventHelpers";
import {
  getWorkflowState,
  updateWorkflowStatus,
  assertWorkflowStatus,
} from "../helpers/workflowHelpers";
import {
  assertEtaWithinBounds,
  assertCriticalPathFormatValid,
  assertPropagationLatencyAcceptable,
} from "../utils/orchestrationAssertions";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { DELAY_PROPAGATION_SCENARIO } from "../fixtures/orchestration-scenarios.mock";
import { SPATIAL_SUMMARY_BIM_LITE } from "../fixtures/spatial-summary.mock";

test.describe("Orchestration: Delay Propagation", () => {
  
  test.beforeEach(async ({ page }) => {
    // Setup mocks avec les données du scénario
    const spatialOverride = {
      spatialSummary: {
        lots: DELAY_PROPAGATION_SCENARIO.initialState.lots.map(lot => ({
          ...lot,
          x: Math.random() * 1000,
          y: Math.random() * 1000,
          z: Math.random() * 100,
        })),
        dependencies: DELAY_PROPAGATION_SCENARIO.initialState.dependencies,
      },
    };
    
    await mockAllApisForSpatialExecution(page, spatialOverride);
    
    // Navigue vers la page d'exécution
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should detect ETA delay on critical lot", async ({ page }) => {
    /**
     * Étape 1: Vérifier l'état initial
     * - Façade ETA = 35j
     * - Chemin critique = [facade, menuiserie, peinture]
     * - Durée = 49j
     */
    const initialTimeline = await getTimelineState(page);
    expect(initialTimeline.facade.eta).toBe(35);
    expect(initialTimeline.criticalPath).toEqual(['facade', 'menuiserie', 'peinture']);
    expect(initialTimeline.criticalPathDuration).toBe(49);
  });

  test("should propagate delay through dependency chain", async ({ page }) => {
    /**
     * Étape 2: Simuler le délai de 13 jours
     * - Façade ETA 35 → 48
     */
    await simulateEtaDelay(page, 13);

    /**
     * Étape 3: Vérifier que l'événement est généré dans l'event feed
     */
    const etaDelayEvent = await waitForEventType(page, 'ETA_DELAY_DETECTED', 5000);
    expect(etaDelayEvent).toBeDefined();
    expect(etaDelayEvent.lot).toBe('facade');
    expect(etaDelayEvent.severity).toBe('CRITICAL');

    /**
     * Étape 4: Vérifier que les ETA dépendants sont recalculés
     * - Menuiserie: 42 → 55 (42 + 13)
     * - Peinture: 49 → 62 (49 + 13)
     */
    await page.waitForTimeout(500);  // Laisser l'orchestration se propager
    
    const timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(48);
    expect(timeline.menuiserie.eta).toBe(55);
    expect(timeline.peinture.eta).toBe(62);
  });

  test("should recalculate critical path after delay", async ({ page }) => {
    /**
     * Étape 5: Simuler délai
     */
    await simulateEtaDelay(page, 13);
    await page.waitForTimeout(500);

    /**
     * Étape 6: Vérifier que CRITICAL_PATH_RECALCULATED événement est généré
     */
    const critPathEvent = await waitForEventType(page, 'CRITICAL_PATH_RECALCULATED', 5000);
    expect(critPathEvent).toBeDefined();

    /**
     * Étape 7: Vérifier que le chemin critique reste le même mais durée augmentée
     */
    const criticalPath = await getCriticalPathLots(page);
    expect(criticalPath).toEqual(['facade', 'menuiserie', 'peinture']);

    const timeline = await getTimelineState(page);
    expect(timeline.criticalPathDuration).toBe(62);  // 49 + 13
  });

  test("should block workflows due to delay", async ({ page }) => {
    /**
     * Étape 8: Simuler le délai
     */
    await simulateEtaDelay(page, 13);
    await page.waitForTimeout(500);

    /**
     * Étape 9: Vérifier que le workflow 'execution' est maintenant bloqué
     */
    const executionWorkflow = await getWorkflowState(page, 'execution');
    expect(executionWorkflow.blocked).toBe(true);
    expect(executionWorkflow.blocker).toContain('delay');

    /**
     * Étape 10: Vérifier que l'événement WORKFLOW_BLOCKED est généré
     */
    const workflowBlockedEvent = await waitForEventType(page, 'WORKFLOW_BLOCKED', 5000);
    expect(workflowBlockedEvent.severity).toBe('CRITICAL');
  });

  test("should trigger planning reflow", async ({ page }) => {
    /**
     * Étape 11: Simuler délai
     */
    await simulateEtaDelay(page, 13);
    await page.waitForTimeout(500);

    /**
     * Étape 12: Vérifier que PLANNING_REFLOW_TRIGGERED événement existe
     */
    const reflowEvent = await waitForEventType(page, 'PLANNING_REFLOW_TRIGGERED', 5000);
    expect(reflowEvent).toBeDefined();

    /**
     * Étape 13: Vérifier que le workflow planning passe à TO_REVIEW
     */
    const planningWorkflow = await getWorkflowState(page, 'planning');
    expect(planningWorkflow.status).toBe('TO_REVIEW');
  });

  test("should maintain event propagation latency SLA", async ({ page }) => {
    /**
     * Étape 14: Simuler délai
     */
    const startTime = Date.now();
    await simulateEtaDelay(page, 13);

    /**
     * Étape 15: Attendre que toutes les événements arrivent
     */
    const events = await getEventFeedFull(page);
    const propagationTime = Date.now() - startTime;

    /**
     * Étape 16: Vérifier que la propagation est dans les temps (< 1000ms)
     */
    await assertPropagationLatencyAcceptable(page, 1000);
  });

  test("should verify complete propagation chain", async ({ page }) => {
    /**
     * Étape 17: Simuler délai
     */
    await simulateEtaDelay(page, 13);
    await page.waitForTimeout(500);

    /**
     * Étape 18: Vérifier la chaîne de propagation complète
     * ETA_DELAY → CRITICAL_PATH_RECALCULATED → WORKFLOW_BLOCKED
     */
    await assertEventPropagation(
      page,
      'ETA_DELAY_DETECTED',
      'WORKFLOW_BLOCKED',
      3  // 3 hops expected
    );

    /**
     * Étape 19: Vérifier que la spatial timeline est aussi mise à jour
     */
    const spatialPath = await getCriticalPathSpatial(page);
    expect(spatialPath.duration).toBe('62');  // 49 + 13
  });

  test("should show all impacted lots in spatial view", async ({ page }) => {
    /**
     * Étape 20: Simuler délai
     */
    await simulateEtaDelay(page, 13);
    await page.waitForTimeout(500);

    /**
     * Étape 21: Vérifier que tous les lots impactés sont marqués dans la vue spatial
     */
    await assertCriticalPathContainsSpatial(page, ['facade', 'menuiserie', 'peinture']);

    /**
     * Étape 22: Vérifier les ETAs dans la vue spatial
     */
    await assertEtaWithinBounds(page, 'facade', 45, 50);   // ~48
    await assertEtaWithinBounds(page, 'menuiserie', 52, 57);  // ~55
    await assertEtaWithinBounds(page, 'peinture', 59, 64);    // ~62
  });

  test("should be reversible (delay removal)", async ({ page }) => {
    /**
     * Étape 23: Simuler délai
     */
    await simulateEtaDelay(page, 13);
    await page.waitForTimeout(500);

    /**
     * Étape 24: Vérifier l'état post-délai
     */
    let timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(48);

    /**
     * Étape 25: Simuler la suppression du délai
     */
    await simulateEtaDelay(page, -13);
    await page.waitForTimeout(500);

    /**
     * Étape 26: Vérifier que tout est revenu à l'état initial
     */
    timeline = await getTimelineState(page);
    expect(timeline.facade.eta).toBe(35);
    expect(timeline.menuiserie.eta).toBe(42);
    expect(timeline.peinture.eta).toBe(49);

    /**
     * Étape 27: Vérifier que workflow n'est plus bloqué
     */
    const executionWorkflow = await getWorkflowState(page, 'execution');
    expect(executionWorkflow.blocked).toBe(false);
  });
});
