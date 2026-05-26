/**
 * non-bim-regression.spec.js
 * 
 * Test compatibilité : NON_BIM regression test
 * Valide que le système fonctionne sans spatial
 */

import { test, expect } from "@playwright/test";
import {
  assertProjectInExecutionMode,
  assertBimMaturityCorrectlyApplied,
} from "../utils/orchestrationAssertions";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { NON_BIM_PROJECT } from "../fixtures/non-bim.mock";

test.describe("Compatibility: NON_BIM Regression", () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAllApisForSpatialExecution(page);
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should work without spatial features", async ({ page }) => {
    /**
     * Étape 1: Vérifier que c'est en mode NON_BIM
     */
    await assertBimMaturityCorrectlyApplied(page, 'NON_BIM');
  });

  test("should not display spatial tab", async ({ page }) => {
    /**
     * Étape 2: Vérifier que tab spatial n'existe pas
     */
    const spatialTab = page.getByTestId("execution-tab-spatial");
    const visible = await spatialTab.isVisible().catch(() => false);
    expect(visible).toBe(false);
  });

  test("should have workflow tab", async ({ page }) => {
    /**
     * Étape 3: Vérifier que workflow existe
     */
    const workflow = page.getByTestId("execution-tab-workflow");
    await expect(workflow).toBeVisible();
  });

  test("should have planning tab", async ({ page }) => {
    /**
     * Étape 4: Vérifier que planning existe
     */
    const planning = page.getByTestId("execution-tab-planning");
    await expect(planning).toBeVisible();
  });

  test("should still have event feed", async ({ page }) => {
    /**
     * Étape 5: Vérifier event feed (non-spatial)
     */
    const eventFeed = page.getByTestId("orchestration-event-feed");
    await expect(eventFeed).toBeVisible();
  });

  test("should still support workflow blocking", async ({ page }) => {
    /**
     * Étape 6: Naviguer à workflow tab
     */
    await page.getByTestId("execution-tab-workflow").click();

    /**
     * Étape 7: Vérifier que workflows existent
     */
    const workflows = page.getByTestId("workflow-board");
    await expect(workflows).toBeVisible();
  });

  test("should still process events", async ({ page }) => {
    /**
     * Étape 8: Vérifier que le feed événementiel fonctionne
     */
    const eventFeed = page.getByTestId("orchestration-event-feed");
    await expect(eventFeed).toBeVisible();

    /**
     * Étape 9: Vérifier qu'il y a au moins un événement
     */
    const events = page.locator('[data-testid="event-item"]');
    const count = await events.count();
    expect(count).toBeGreaterThan(0);
  });

  test("should not crash on missing spatial data", async ({ page }) => {
    /**
     * Étape 10: Les pages critiques doivent rester accessibles
     */
    const overview = page.getByTestId("project-overview-card");
    await expect(overview).toBeVisible();

    const workflow = page.getByTestId("execution-tab-workflow");
    await expect(workflow).toBeVisible();

    /**
     * Étape 11: Pas d'erreur console
     */
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Navigation to workflow
    await workflow.click();
    await page.waitForTimeout(500);

    expect(errors.filter(e => e.includes('Cannot read')).length).toBe(0);
  });
});
