/**
 * scenario-storage-conflict.spec.js
 * 
 * Test d'orchestration : conflit de stockage
 * Scénario: Zone saturée à 95% → actions de déplacement/report livraisons
 * 
 * Cela valide:
 * - Détection saturation stockage
 * - Génération d'actions STORAGE
 * - Recalcul des livraisons
 * - Blocage workflow de livraison
 * - Recommandations d'arbitrage
 */

import { test, expect } from "@playwright/test";
import {
  simulateStorageConflict,
  saturateStorage,
  getStorageHeatmap,
  waitForEventInFeed,
} from "../helpers/orchestrationHelpers";
import {
  getStorageHeatmap as getSpatialStorageHeatmap,
  assertStorageSaturated,
} from "../helpers/spatialHelpers";
import {
  getEventFeedFull,
  waitForEventType,
} from "../helpers/eventHelpers";
import {
  getWorkflowState,
  assertWorkflowStatus,
  getBlockedWorkflows,
} from "../helpers/workflowHelpers";
import {
  assertStorageZoneSaturated,
} from "../utils/orchestrationAssertions";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { STORAGE_CONFLICT_SCENARIO } from "../fixtures/orchestration-scenarios.mock";

test.describe("Orchestration: Storage Conflict", () => {
  
  test.beforeEach(async ({ page }) => {
    // Setup mocks
    const storageOverride = {
      storageHeatmap: [
        { zone: 'reception', saturation: 0.65, conflicts: 0 },
        { zone: 'stockage', saturation: 0.85, conflicts: 2 },
        { zone: 'stockage_overflow', saturation: 0.45, conflicts: 0 },
      ],
    };
    
    await mockAllApisForSpatialExecution(page, storageOverride);
    
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should detect storage saturation", async ({ page }) => {
    /**
     * Étape 1: Vérifier l'état initial
     * - Zone stockage = 85% (WARNING)
     */
    const heatmap = await getStorageHeatmap(page);
    const stockageZone = heatmap.find(z => z.zone === 'stockage');
    expect(stockageZone.saturation).toBe(0.85);
    expect(stockageZone.alert).toBe('WARNING');
  });

  test("should trigger critical alert when saturation exceeds 90%", async ({ page }) => {
    /**
     * Étape 2: Augmenter la saturation à 95%
     */
    await saturateStorage(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 3: Vérifier que l'événement STORAGE_SATURATION_CRITICAL est généré
     */
    const criticalEvent = await waitForEventType(page, 'STORAGE_SATURATION_CRITICAL', 5000);
    expect(criticalEvent).toBeDefined();
    expect(criticalEvent.zone).toBe('stockage');
    expect(criticalEvent.severity).toBe('CRITICAL');

    /**
     * Étape 4: Vérifier que la heatmap est mise à jour
     */
    const updatedHeatmap = await getStorageHeatmap(page);
    const zone = updatedHeatmap.find(z => z.zone === 'stockage');
    expect(zone.saturation).toBeGreaterThanOrEqual(0.90);
    expect(zone.alert).toBe('CRITICAL');
  });

  test("should generate STORAGE type actions", async ({ page }) => {
    /**
     * Étape 5: Déclencher le conflit
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 6: Vérifier que des actions STORAGE sont générées
     */
    const storageActions = await page.evaluate(() => {
      return Array.from(
        document.querySelectorAll('[data-testid="action"][data-action-type="STORAGE"]')
      ).map(el => ({
        id: el.dataset.actionId,
        title: el.textContent,
        priority: el.dataset.priority,
      }));
    });

    expect(storageActions.length).toBeGreaterThan(0);
    expect(storageActions[0].priority).toBe('CRITICAL');
  });

  test("should block delivery workflow", async ({ page }) => {
    /**
     * Étape 7: Déclencher conflit
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 8: Vérifier que le workflow delivery est bloqué
     */
    const deliveryWorkflow = await getWorkflowState(page, 'delivery');
    expect(deliveryWorkflow).toBeDefined();
    expect(deliveryWorkflow.blocked).toBe(true);
    expect(deliveryWorkflow.blocker).toContain('storage');

    /**
     * Étape 9: Vérifier l'événement WORKFLOW_BLOCKED
     */
    const blockedEvent = await waitForEventType(page, 'WORKFLOW_BLOCKED', 5000);
    expect(blockedEvent).toBeDefined();
  });

  test("should suggest delivery deferment", async ({ page }) => {
    /**
     * Étape 10: Déclencher conflit
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 11: Vérifier que les recommandations incluent DEFER_DELIVERY
     */
    const actions = await page.evaluate(() => {
      return Array.from(
        document.querySelectorAll('[data-testid="action"][data-action-type="STORAGE"]')
      ).map(el => ({
        recommendations: el.dataset.recommendations?.split(',') || [],
      }));
    });

    expect(actions.length).toBeGreaterThan(0);
    expect(actions[0].recommendations).toContain('DEFER_DELIVERY');
  });

  test("should suggest delivery splitting", async ({ page }) => {
    /**
     * Étape 12: Déclencher conflit
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 13: Vérifier que les recommandations incluent SPLIT_DELIVERY
     */
    const actions = await page.evaluate(() => {
      return Array.from(
        document.querySelectorAll('[data-testid="action"][data-action-type="STORAGE"]')
      ).map(el => ({
        recommendations: el.dataset.recommendations?.split(',') || [],
      }));
    });

    expect(actions[0].recommendations).toContain('SPLIT_DELIVERY');
  });

  test("should trigger planning review workflow", async ({ page }) => {
    /**
     * Étape 14: Déclencher conflit
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 15: Vérifier que le workflow planning passe à TO_REVIEW
     */
    const planningWorkflow = await getWorkflowState(page, 'planning');
    expect(planningWorkflow.status).toBe('TO_REVIEW');

    /**
     * Étape 16: Vérifier que l'événement est généré
     */
    await waitForEventType(page, 'PLANNING_REVIEW_TRIGGERED', 5000);
  });

  test("should show zone conflicts in spatial heatmap", async ({ page }) => {
    /**
     * Étape 17: Déclencher conflit
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 18: Vérifier la heatmap spatial
     */
    const spatialHeatmap = await getSpatialStorageHeatmap(page);
    const criticalZone = spatialHeatmap.find(z => z.zone === 'stockage');
    
    expect(criticalZone).toBeDefined();
    expect(criticalZone.saturation).toBeGreaterThanOrEqual(0.90);
    expect(criticalZone.alert).toBe('CRITICAL');
  });

  test("should track conflict resolution", async ({ page }) => {
    /**
     * Étape 19: Déclencher conflit
     */
    await simulateStorageConflict(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 20: Récupérer l'action générée
     */
    const actions = await page.evaluate(() => {
      return Array.from(
        document.querySelectorAll('[data-testid="action"][data-action-type="STORAGE"]')
      ).map(el => ({
        id: el.dataset.actionId,
      }));
    });

    expect(actions.length).toBeGreaterThan(0);
    const actionId = actions[0].id;

    /**
     * Étape 21: Marquer l'action comme terminée
     */
    await page.evaluate(({ id }) => {
      window.dispatchEvent(new CustomEvent('orchestration:action-completed', {
        detail: { actionId: id }
      }));
    }, { id: actionId });

    await page.waitForTimeout(500);

    /**
     * Étape 22: Vérifier que le workflow peut progresser à nouveau
     */
    const deliveryWorkflow = await getWorkflowState(page, 'delivery');
    // Après résolution, le workflow ne doit plus être bloqué par ce conflit
    expect(deliveryWorkflow.blocked).toBe(false);
  });

  test("should prevent zone overflow", async ({ page }) => {
    /**
     * Étape 23: Vérifier que stockage_overflow reste disponible
     */
    const initialHeatmap = await getStorageHeatmap(page);
    const overflowZone = initialHeatmap.find(z => z.zone === 'stockage_overflow');
    expect(overflowZone.saturation).toBeLessThan(0.70);

    /**
     * Étape 24: Saturer la zone principale
     */
    await saturateStorage(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 25: Vérifier que l'overflow peut accueillir les déplacements
     */
    const updatedHeatmap = await getStorageHeatmap(page);
    const updatedOverflow = updatedHeatmap.find(z => z.zone === 'stockage_overflow');
    expect(updatedOverflow).toBeDefined();
  });

  test("should be reversible (desaturation)", async ({ page }) => {
    /**
     * Étape 26: Saturer
     */
    await saturateStorage(page, 0.95);
    await page.waitForTimeout(500);

    /**
     * Étape 27: Vérifier l'état saturé
     */
    let heatmap = await getStorageHeatmap(page);
    let zone = heatmap.find(z => z.zone === 'stockage');
    expect(zone.saturation).toBeGreaterThanOrEqual(0.90);

    /**
     * Étape 28: Désaturer
     */
    await saturateStorage(page, 0.65);
    await page.waitForTimeout(500);

    /**
     * Étape 29: Vérifier le retour à la normal
     */
    heatmap = await getStorageHeatmap(page);
    zone = heatmap.find(z => z.zone === 'stockage');
    expect(zone.saturation).toBeLessThan(0.80);

    /**
     * Étape 30: Vérifier que workflow n'est plus bloqué
     */
    const deliveryWorkflow = await getWorkflowState(page, 'delivery');
    expect(deliveryWorkflow.blocked).toBe(false);
  });
});
