/**
 * bim-lite-regression.spec.js
 * 
 * Test compatibilité : BIM_LITE regression test
 * Valide que toutes les fonctionnalités BIM-LITE fonctionnent
 */

import { test, expect } from "@playwright/test";
import {
  openSpatialTab,
  expectSpatialTabVisible,
} from "../helpers/spatialHelpers";
import {
  assertProjectInExecutionMode,
  assertBimMaturityCorrectlyApplied,
} from "../utils/orchestrationAssertions";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { BIM_LITE_PROJECT } from "../fixtures/bim-lite.mock";

test.describe("Compatibility: BIM_LITE Regression", () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAllApisForSpatialExecution(page);
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should be in BIM_LITE mode", async ({ page }) => {
    /**
     * Étape 1: Vérifier maturité BIM
     */
    await assertBimMaturityCorrectlyApplied(page, 'BIM_LITE');
  });

  test("should have spatial timeline enabled", async ({ page }) => {
    /**
     * Étape 2: Vérifier que spatial tab est visible
     */
    const visible = await expectSpatialTabVisible(page);
    expect(visible).toBe(true);
  });

  test("should have storage heatmap", async ({ page }) => {
    /**
     * Étape 3: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 4: Vérifier que heatmap existe
     */
    const heatmapElement = page.getByTestId("spatial-heatmap");
    await expect(heatmapElement).toBeVisible();
  });

  test("should have workflow blocking", async ({ page }) => {
    /**
     * Étape 5: Vérifier que workflows sont créés
     */
    const workflows = page.getByTestId("execution-tab-workflow");
    await expect(workflows).toBeVisible();
  });

  test("should have event feed", async ({ page }) => {
    /**
     * Étape 6: Vérifier que event feed existe
     */
    const eventFeed = page.getByTestId("orchestration-event-feed");
    await expect(eventFeed).toBeVisible();
  });

  test("should not have 3D model view", async ({ page }) => {
    /**
     * Étape 7: Vérifier que 3D n'est pas disponible en BIM_LITE
     */
    const model3d = page.getByTestId("execution-tab-3d-model");
    const visible = await model3d.isVisible().catch(() => false);
    expect(visible).toBe(false);
  });

  test("should not have component-level drilldown", async ({ page }) => {
    /**
     * Étape 8: Vérifier que component drilldown n'existe pas
     */
    const componentDrilldown = page.getByTestId("component-level-drilldown");
    const visible = await componentDrilldown.isVisible().catch(() => false);
    expect(visible).toBe(false);
  });

  test("should have basic dependencies", async ({ page }) => {
    /**
     * Étape 9: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 10: Vérifier que dépendances sont visibles
     */
    const depsElement = page.getByTestId("spatial-dependencies");
    await expect(depsElement).toBeVisible();
  });

  test("should be fully functional end-to-end", async ({ page }) => {
    /**
     * Étape 11: Vérifier workflow visible
     */
    const workflow = page.getByTestId("execution-tab-workflow");
    await expect(workflow).toBeVisible();

    /**
     * Étape 12: Vérifier planning visible
     */
    const planning = page.getByTestId("execution-tab-planning");
    await expect(planning).toBeVisible();

    /**
     * Étape 13: Vérifier livraisons visible
     */
    const deliveries = page.getByTestId("execution-tab-deliveries");
    await expect(deliveries).toBeVisible();
  });
});
