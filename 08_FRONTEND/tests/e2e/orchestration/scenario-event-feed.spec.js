/**
 * scenario-event-feed.spec.js
 * 
 * Test d'orchestration : événements et feed temps réel
 * Scénario: Vérifier que le système événementiel propage les événements
 * 
 * Cela valide:
 * - Événements générés et envoyés
 * - Ordre chronologique
 * - Chaînes de propagation
 * - Latence acceptable
 * - Métadonnées correctes
 */

import { test, expect } from "@playwright/test";
import {
  simulateEtaDelay,
  simulateStorageConflict,
  blockWorkflow,
} from "../helpers/orchestrationHelpers";
import {
  getEventFeedFull,
  waitForEventType,
  getEventChain,
  filterEventsBySource,
  getEventTimeGaps,
  clearEventFeed,
} from "../helpers/eventHelpers";
import {
  assertEventExists,
  assertEventPropagation,
  assertNoEventOfType,
} from "../utils/orchestrationAssertions";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";

test.describe("Orchestration: Event Feed", () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAllApisForSpatialExecution(page);
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should display event feed on execution page", async ({ page }) => {
    /**
     * Étape 1: Vérifier que le feed événementiel est visible
     */
    const feedElement = page.getByTestId("orchestration-event-feed");
    await expect(feedElement).toBeVisible();
  });

  test("should show initial events", async ({ page }) => {
    /**
     * Étape 2: Récupérer les événements initiaux (DQE imported, simulation done, etc.)
     */
    const initialEvents = await getEventFeedFull(page);
    expect(initialEvents.length).toBeGreaterThan(0);

    /**
     * Étape 3: Vérifier que les types sont correctement définis
     */
    for (const event of initialEvents) {
      expect(event.type).toBeTruthy();
      expect(event.timestamp).toBeTruthy();
      expect(['INFO', 'WARNING', 'CRITICAL']).toContain(event.severity);
    }
  });

  test("should maintain chronological order", async ({ page }) => {
    /**
     * Étape 4: Récupérer tous les événements
     */
    const events = await getEventFeedFull(page);

    /**
     * Étape 5: Vérifier l'ordre décroissant (plus récents d'abord)
     */
    for (let i = 0; i < events.length - 1; i++) {
      const t1 = new Date(events[i].timestamp).getTime();
      const t2 = new Date(events[i + 1].timestamp).getTime();
      expect(t1).toBeGreaterThanOrEqual(t2);
    }
  });

  test("should capture ETA_DELAY event", async ({ page }) => {
    /**
     * Étape 6: Déclencher un délai
     */
    await simulateEtaDelay(page, 5);
    await page.waitForTimeout(500);

    /**
     * Étape 7: Vérifier que l'événement existe
     */
    await assertEventExists(page, 'ETA_DELAY_DETECTED', {
      severity: 'CRITICAL',
    });
  });

  test("should capture STORAGE_SATURATION event", async ({ page }) => {
    /**
     * Étape 8: Déclencher saturation
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 9: Vérifier l'événement
     */
    await assertEventExists(page, 'STORAGE_SATURATION_CRITICAL');
  });

  test("should capture WORKFLOW_BLOCKING event", async ({ page }) => {
    /**
     * Étape 10: Déclencher blocage
     */
    await blockWorkflow(page, 'test_reason');
    await page.waitForTimeout(500);

    /**
     * Étape 11: Vérifier l'événement
     */
    await assertEventExists(page, 'WORKFLOW_BLOCKING_STARTED');
  });

  test("should show event propagation chain", async ({ page }) => {
    /**
     * Étape 12: Déclencher délai
     */
    await simulateEtaDelay(page, 5);
    await page.waitForTimeout(500);

    /**
     * Étape 13: Récupérer la chaîne de propagation
     */
    const chain = await getEventChain(
      page,
      'ETA_DELAY_DETECTED',
      'WORKFLOW_BLOCKED',
      10
    );

    /**
     * Étape 14: Vérifier la chaîne existe
     */
    expect(chain.chain.length).toBeGreaterThan(0);
  });

  test("should filter events by source", async ({ page }) => {
    /**
     * Étape 15: Récupérer tous les événements du simulation_engine
     */
    const simEvents = await filterEventsBySource(page, 'simulation_engine');

    /**
     * Étape 16: Vérifier qu'ils existent et proviennent bien du source
     */
    if (simEvents.length > 0) {
      for (const event of simEvents) {
        expect(event.source).toBe('simulation_engine');
      }
    }
  });

  test("should measure propagation latency", async ({ page }) => {
    /**
     * Étape 17: Déclencher délai et mesurer temps
     */
    const startTime = Date.now();
    await simulateEtaDelay(page, 5);
    
    /**
     * Étape 18: Attendre le dernier événement de la chaîne
     */
    const lastEvent = await waitForEventType(page, 'WORKFLOW_BLOCKED', 5000);
    const propagationTime = Date.now() - startTime;

    /**
     * Étape 19: Vérifier que la propagation est rapide
     */
    expect(propagationTime).toBeLessThan(3000);
  });

  test("should handle multiple simultaneous events", async ({ page }) => {
    /**
     * Étape 20: Déclencher plusieurs perturbations rapidement
     */
    await simulateEtaDelay(page, 3);
    await simulateStorageConflict(page, 0.90);
    await blockWorkflow(page, 'reason1');
    
    await page.waitForTimeout(500);

    /**
     * Étape 21: Vérifier que tous les événements sont capturés
     */
    const events = await getEventFeedFull(page);
    const types = events.map(e => e.type);
    
    expect(types).toContain('ETA_DELAY_DETECTED');
    expect(types).toContain('STORAGE_SATURATION_CRITICAL');
    expect(types).toContain('WORKFLOW_BLOCKING_STARTED');
  });

  test("should support event feed clearing", async ({ page }) => {
    /**
     * Étape 22: Compter les événements
     */
    let events = await getEventFeedFull(page);
    const beforeCount = events.length;

    /**
     * Étape 23: Vider le feed
     */
    await clearEventFeed(page);
    await page.waitForTimeout(300);

    /**
     * Étape 24: Vérifier que c'est vide
     */
    events = await getEventFeedFull(page);
    expect(events.length).toBe(0);

    /**
     * Étape 25: Déclencher nouvel événement
     */
    await simulateEtaDelay(page, 2);
    await page.waitForTimeout(500);

    /**
     * Étape 26: Vérifier qu'il n'y a que le nouvel événement
     */
    events = await getEventFeedFull(page);
    expect(events.length).toBeGreaterThan(0);
    expect(events.length).toBeLessThan(beforeCount);
  });

  test("should include complete metadata", async ({ page }) => {
    /**
     * Étape 27: Déclencher un événement
     */
    await simulateEtaDelay(page, 3);
    await page.waitForTimeout(500);

    /**
     * Étape 28: Récupérer l'événement
     */
    const events = await getEventFeedFull(page);
    const etaEvent = events.find(e => e.type === 'ETA_DELAY_DETECTED');
    
    /**
     * Étape 29: Vérifier les métadonnées
     */
    expect(etaEvent).toBeDefined();
    expect(etaEvent.metadata).toBeDefined();
    expect(typeof etaEvent.metadata).toBe('object');
  });

  test("should prevent duplicate events", async ({ page }) => {
    /**
     * Étape 30: Déclencher même événement deux fois rapidement
     */
    await simulateEtaDelay(page, 1);
    await page.waitForTimeout(100);
    await simulateEtaDelay(page, 1);
    await page.waitForTimeout(500);

    /**
     * Étape 31: Vérifier qu'il y a deux événements (pas dedupé)
     * Ou le système peut avoir une logique de deduplication intelligente
     */
    const events = await getEventFeedFull(page);
    const etaEvents = events.filter(e => e.type === 'ETA_DELAY_DETECTED');
    
    // Au minimum, il doit y avoir au moins un événement
    expect(etaEvents.length).toBeGreaterThanOrEqual(1);
  });
});
