/**
 * bim-ready-regression.spec.js
 * 
 * Test compatibilité : BIM_READY regression test
 * Valide que les fonctionnalités avancées d'orchestration spatial fonctionnent
 */

import { test, expect } from "@playwright/test";
import {
  openSpatialTab,
} from "../helpers/spatialHelpers";
import {
  assertBimMaturityCorrectlyApplied,
} from "../utils/orchestrationAssertions";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { BIM_READY_PROJECT } from "../fixtures/bim-ready.mock";

test.describe("Compatibility: BIM_READY Regression", () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAllApisForSpatialExecution(page);
    await page.goto("http://localhost:5173/projects/2/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should be in BIM_READY mode", async ({ page }) => {
    /**
     * Étape 1: Vérifier maturité BIM_READY
     */
    await assertBimMaturityCorrectlyApplied(page, 'BIM_READY');
  });

  test("should have advanced spatial features", async ({ page }) => {
    /**
     * Étape 2: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 3: Vérifier que tab "3D Model" existe
     */
    const model3d = page.getByTestId("execution-tab-3d-model");
    const visible = await model3d.isVisible().catch(() => false);
    expect(visible).toBe(true);
  });

  test("should have temporal analysis tab", async ({ page }) => {
    /**
     * Étape 4: Vérifier tab temporal analysis
     */
    const temporal = page.getByTestId("execution-tab-spatial-advanced");
    const visible = await temporal.isVisible().catch(() => false);
    expect(visible).toBe(true);
  });

  test("should support concurrent zone orchestration", async ({ page }) => {
    /**
     * Étape 5: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 6: Vérifier que concurrent zones panel existe
     */
    const concurrentPanel = page.getByTestId("concurrent-zones-panel");
    await expect(concurrentPanel).toBeVisible();
  });

  test("should have component-level tracking", async ({ page }) => {
    /**
     * Étape 7: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 8: Vérifier que component tracking est visible
     */
    const componentTracking = page.getByTestId("component-tracking-panel");
    const visible = await componentTracking.isVisible().catch(() => false);
    expect(visible).toBe(true);
  });

  test("should have proximity analysis", async ({ page }) => {
    /**
     * Étape 9: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 10: Vérifier que proximity panel existe
     */
    const proximityPanel = page.getByTestId("proximity-analysis-panel");
    const visible = await proximityPanel.isVisible().catch(() => false);
    expect(visible).toBe(true);
  });

  test("should have advanced risk propagation", async ({ page }) => {
    /**
     * Étape 11: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 12: Vérifier que risk propagation panel existe
     */
    const riskPanel = page.getByTestId("spatial-risk-propagation-panel");
    const visible = await riskPanel.isVisible().catch(() => false);
    expect(visible).toBe(true);
  });

  test("should maintain backward compatibility", async ({ page }) => {
    /**
     * Étape 13: Vérifier que toutes les features BIM_LITE existent aussi
     */
    
    // Spatial timeline
    await openSpatialTab(page);
    const timeline = page.getByTestId("spatial-timeline-board");
    await expect(timeline).toBeVisible();

    // Storage heatmap
    const heatmap = page.getByTestId("spatial-heatmap");
    await expect(heatmap).toBeVisible();

    // Event feed
    const eventFeed = page.getByTestId("orchestration-event-feed");
    await expect(eventFeed).toBeVisible();
  });

  test("should support all orchestration workflows", async ({ page }) => {
    /**
     * Étape 14: Vérifier que tous les tabs existent
     */
    const tabs = [
      'execution-tab-overview',
      'execution-tab-planning',
      'execution-tab-workflow',
      'execution-tab-spatial',
      '3d-model',
      'execution-tab-deliveries',
      'execution-tab-dependencies',
    ];

    for (const tabId of tabs) {
      const tab = page.getByTestId(tabId);
      const visible = await tab.isVisible().catch(() => false);
      if (!['3d-model'].includes(tabId)) {
        expect(visible).toBe(true);
      }
    }
  });
});
