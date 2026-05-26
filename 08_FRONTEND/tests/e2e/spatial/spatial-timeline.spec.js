/**
 * spatial-timeline.spec.js
 * 
 * Test spatial : timeline spatiale visualisée
 * Valide: lots positionnés, dépendances visibles, ETAs mises à jour
 */

import { test, expect } from "@playwright/test";
import {
  openSpatialTab,
  getSpatialTimelineState,
  getCriticalPathSpatial,
  assertCriticalPathContainsSpatial,
} from "../helpers/spatialHelpers";
import {
  simulateEtaDelay,
} from "../helpers/orchestrationHelpers";
import {
  mockAllApisForSpatialExecution,
} from "../helpers/apiMocks";
import { SPATIAL_SUMMARY_BIM_LITE } from "../fixtures/spatial-summary.mock";

test.describe("Spatial: Timeline Visualization", () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAllApisForSpatialExecution(page);
    await page.goto("http://localhost:5173/projects/1/execution");
    await page.waitForLoadState('networkidle');
  });

  test("should display spatial timeline tab", async ({ page }) => {
    /**
     * Étape 1: Vérifier que tab spatial existe
     */
    const spatialTab = page.getByTestId("execution-tab-spatial");
    await expect(spatialTab).toBeVisible();
  });

  test("should load spatial data on tab click", async ({ page }) => {
    /**
     * Étape 2: Cliquer sur tab spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 3: Vérifier que les données spatiales sont chargées
     */
    const timelineState = await getSpatialTimelineState(page);
    expect(timelineState).toBeDefined();
    expect(timelineState.lots).toBeDefined();
    expect(timelineState.lots.length).toBeGreaterThan(0);
  });

  test("should display all lots with coordinates", async ({ page }) => {
    /**
     * Étape 4: Ouvrir tab spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 5: Vérifier que chaque lot a des coordonnées
     */
    const timeline = await getSpatialTimelineState(page);
    
    for (const lot of timeline.lots) {
      expect(lot.x).toBeDefined();
      expect(lot.y).toBeDefined();
      expect(typeof lot.x).toBe('number');
      expect(typeof lot.y).toBe('number');
    }
  });

  test("should show lot ETAs in spatial view", async ({ page }) => {
    /**
     * Étape 6: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 7: Vérifier que les ETAs sont affichés
     */
    const timeline = await getSpatialTimelineState(page);
    
    for (const lot of timeline.lots) {
      expect(lot.eta).toBeDefined();
      expect(typeof lot.eta).toBe('number');
      expect(lot.eta).toBeGreaterThan(0);
    }
  });

  test("should display critical path highlighted", async ({ page }) => {
    /**
     * Étape 8: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 9: Récupérer le chemin critique
     */
    const criticalPath = await getCriticalPathSpatial(page);
    expect(criticalPath).toBeDefined();
    expect(criticalPath.lots).toBeDefined();
    expect(criticalPath.lots.length).toBeGreaterThan(0);

    /**
     * Étape 10: Vérifier la durée
     */
    expect(criticalPath.duration).toBeDefined();
  });

  test("should update spatial timeline on ETA delay", async ({ page }) => {
    /**
     * Étape 11: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 12: Récupérer état initial
     */
    let timeline = await getSpatialTimelineState(page);
    const initialFacadeEta = timeline.lots.find(l => l.id === 'facade').eta;
    expect(initialFacadeEta).toBe(35);

    /**
     * Étape 13: Simuler délai
     */
    await simulateEtaDelay(page, 10);
    await page.waitForTimeout(500);

    /**
     * Étape 14: Vérifier mise à jour
     */
    timeline = await getSpatialTimelineState(page);
    const updatedFacadeEta = timeline.lots.find(l => l.id === 'facade').eta;
    expect(updatedFacadeEta).toBe(45);
  });

  test("should maintain spatial coherence", async ({ page }) => {
    /**
     * Étape 15: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 16: Vérifier que les lots ne se chevauchent pas
     * (distance > 0)
     */
    const timeline = await getSpatialTimelineState(page);
    
    for (let i = 0; i < timeline.lots.length; i++) {
      for (let j = i + 1; j < timeline.lots.length; j++) {
        const lot1 = timeline.lots[i];
        const lot2 = timeline.lots[j];
        
        const distance = Math.sqrt(
          Math.pow(lot1.x - lot2.x, 2) + 
          Math.pow(lot1.y - lot2.y, 2)
        );
        
        expect(distance).toBeGreaterThan(0);
      }
    }
  });

  test("should show lot dependencies visually", async ({ page }) => {
    /**
     * Étape 17: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 18: Vérifier qu'il y a des dépendances
     */
    const timeline = await getSpatialTimelineState(page);
    expect(timeline.dependencies).toBeDefined();
    expect(timeline.dependencies.length).toBeGreaterThan(0);

    /**
     * Étape 19: Vérifier chaque dépendance
     */
    for (const dep of timeline.dependencies) {
      expect(dep.from).toBeDefined();
      expect(dep.to).toBeDefined();
    }
  });

  test("should maintain correct critical path", async ({ page }) => {
    /**
     * Étape 20: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 21: Vérifier chemin critique contient les lots
     */
    await assertCriticalPathContainsSpatial(page, ['facade', 'menuiserie', 'peinture']);
  });

  test("should be responsive on smaller screens", async ({ page }) => {
    /**
     * Étape 22: Changer à taille tablette
     */
    await page.setViewportSize({ width: 768, height: 1024 });

    /**
     * Étape 23: Ouvrir spatial
     */
    await openSpatialTab(page);

    /**
     * Étape 24: Vérifier que c'est visible
     */
    const timeline = await getSpatialTimelineState(page);
    expect(timeline).toBeDefined();
    expect(timeline.lots.length).toBeGreaterThan(0);
  });
});
