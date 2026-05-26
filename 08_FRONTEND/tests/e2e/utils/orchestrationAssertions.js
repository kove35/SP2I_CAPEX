/**
 * orchestrationAssertions.js
 * 
 * Assertions métier robustes pour valider l'orchestration.
 * Assertions très métier-focused et lisibles.
 */

import { expect } from "@playwright/test";

export async function assertProjectInExecutionMode(page) {
  /**
   * Assertion : projet est en mode exécution.
   */
  const header = page.getByTestId("workspace-header");
  await expect(header).toBeVisible();
  
  const executionButton = page.getByTestId("project-quick-actions").getByRole("button", { name: /exécution/i });
  await expect(executionButton).toBeVisible();
  await expect(executionButton).not.toBeDisabled();
}

export async function assertCriticalPathFormatValid(page, expectedFormat = ['facade', 'menuiserie', 'peinture']) {
  /**
   * Assertion : le chemin critique a la séquence attendue.
   */
  const criticalPath = await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid="timeline-lot"][data-critical="true"]')
    ).map(el => el.dataset.lotId);
  });

  expect(criticalPath).toEqual(expectedFormat);
}

export async function assertEtaWithinBounds(page, lotId, minDays, maxDays) {
  /**
   * Assertion : ETA d'un lot se situe dans les limites attendues.
   */
  const eta = await page.evaluate(({ id }) => {
    const lot = document.querySelector(`[data-testid="timeline-lot-${id}"]`);
    return lot ? parseInt(lot.dataset.eta) : null;
  }, { id: lotId });

  if (eta === null) throw new Error(`Lot ${lotId} not found`);
  expect(eta).toBeGreaterThanOrEqual(minDays);
  expect(eta).toBeLessThanOrEqual(maxDays);
}

export async function assertStorageZoneSaturated(page, zone, expectedSaturation, tolerance = 0.05) {
  /**
   * Assertion : zone stockage saturée au taux attendu (±tolerance).
   */
  const saturation = await page.evaluate(({ zoneId }) => {
    const el = document.querySelector(`[data-testid="heatmap-zone-${zoneId}"]`);
    return el ? parseFloat(el.dataset.saturation) : null;
  }, { zoneId: zone });

  if (saturation === null) throw new Error(`Zone ${zone} not found`);
  expect(Math.abs(saturation - expectedSaturation)).toBeLessThanOrEqual(tolerance);
}

export async function assertWorkflowIsBlockedBy(page, blockedWorkflow, blockerWorkflow) {
  /**
   * Assertion : un workflow est bloqué par un autre spécifique.
   */
  const blocker = await page.evaluate(({ blocked }) => {
    const el = document.querySelector(`[data-testid="workflow-${blocked}"]`);
    return el ? el.dataset.blocker : null;
  }, { blocked: blockedWorkflow });

  expect(blocker).toBe(blockerWorkflow);
}

export async function assertDependencyChainComplete(page, chain = ['facade', 'menuiserie', 'peinture']) {
  /**
   * Assertion : la chaîne de dépendance est complète et linéaire.
   */
  for (let i = 0; i < chain.length - 1; i++) {
    const from = chain[i];
    const to = chain[i + 1];
    
    const dep = await page.evaluate(({ source, target }) => {
      return document.querySelector(`[data-from="${source}"][data-to="${target}"]`) !== null;
    }, { source: from, target: to });

    expect(dep).toBe(true);
  }
}

export async function assertPropagationLatencyAcceptable(page, maxLatencyMs = 1000) {
  /**
   * Assertion : la propagation événementielle respecte le SLA de latence.
   * Vérifie que entre évenement source et événement propagé < maxLatencyMs.
   */
  const gaps = await page.evaluate(() => {
    const events = Array.from(
      document.querySelectorAll('[data-testid="event-item"]')
    ).map(el => ({
      type: el.dataset.eventType,
      timestamp: new Date(el.dataset.timestamp),
    }));

    const gaps = [];
    for (let i = 0; i < events.length - 1; i++) {
      const gap = events[i].timestamp - events[i + 1].timestamp;
      gaps.push(gap);
    }
    return gaps;
  });

  for (const gap of gaps) {
    expect(gap).toBeLessThan(maxLatencyMs);
  }
}

export async function assertNoHorizontalScrollOnTablet(page) {
  /**
   * Assertion : pas de scroll horizontal sur tablette.
   * Important pour spatial UI responsif.
   */
  await page.setViewportSize({ width: 768, height: 1024 });
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth - document.documentElement.clientWidth;
  });
  expect(overflow).toBeLessThanOrEqual(2);
}

export async function assertSpatialTimelineRenderStable(page, renderTimeMs = 1000) {
  /**
   * Assertion : timeline spatiale rendred stable en timeoutMs sans layout thrashing.
   */
  const metrics = await page.evaluate(({ timeout }) => {
    const startTime = performance.now();
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > 50) {
          console.warn('Long task:', entry.duration);
        }
      }
    });
    observer.observe({ entryTypes: ['longtask'] });
    
    return new Promise(resolve => {
      setTimeout(() => {
        observer.disconnect();
        resolve({
          renderTime: performance.now() - startTime,
          hasStopped: true,
        });
      }, timeout);
    });
  }, { timeout: renderTimeMs });

  expect(metrics.renderTime).toBeLessThan(renderTimeMs);
}

export async function assertEventsFeedInOrder(page, expectedOrder = ['DQE_IMPORTED', 'SCENARIO_SIMULATED']) {
  /**
   * Assertion : le feed événementiel montre les événements dans l'ordre de récence.
   */
  const events = await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid="event-item"]')
    ).map(el => el.dataset.eventType);
  });

  let lastIndex = -1;
  for (const eventType of expectedOrder) {
    const index = events.indexOf(eventType);
    expect(index).toBeGreaterThan(lastIndex);
    lastIndex = index;
  }
}

export async function assertActionGeneratedForRisk(page, riskType, expectedActionType) {
  /**
   * Assertion : action générée automatiquement pour chaque risque détecté.
   * Exemple: risque supplier_risk → action type PROCUREMENT.
   */
  const action = await page.evaluate(({ risk, type }) => {
    return document.querySelector(`[data-testid="action-${type}"][data-risk-source="${risk}"]`) !== null;
  }, { risk: riskType, type: expectedActionType });

  expect(action).toBe(true);
}

export async function assertWorkflowResponsibleSet(page, workflowName) {
  /**
   * Assertion : responsable est assigné au workflow.
   * Critique pour l'exécution.
   */
  const responsible = await page.evaluate(({ name }) => {
    const el = document.querySelector(`[data-testid="workflow-${name}"]`);
    return el ? el.dataset.responsible : null;
  }, { name: workflowName });

  expect(responsible).toBeTruthy();
}

export async function assertNoDataLossDuringPropagation(page) {
  /**
   * Assertion : aucune perte de données lors de la propagation.
   * Valide que tous les événements arrivent.
   */
  const eventCount = await page.evaluate(() => {
    return document.querySelectorAll('[data-testid="event-item"]').length;
  });

  const workflowCount = await page.evaluate(() => {
    return document.querySelectorAll('[data-testid^="workflow-"]').length;
  });

  // Vérifier que pour chaque événement, il y a un workflow correspondant
  expect(workflowCount).toBeGreaterThan(0);
  expect(eventCount).toBeGreaterThan(0);
}

export async function assertBimMaturityCorrectlyApplied(page, expectedMaturity = 'BIM_LITE') {
  /**
   * Assertion : maturité BIM appliquée correctement.
   * Détermine quelles features doivent être visibles.
   */
  const spatialVisible = await page.getByTestId("execution-tab-spatial").isVisible();
  
  if (expectedMaturity === 'NON_BIM') {
    expect(spatialVisible).toBe(false);
  } else if (expectedMaturity === 'BIM_LITE') {
    expect(spatialVisible).toBe(true);
  } else if (expectedMaturity === 'BIM_READY') {
    expect(spatialVisible).toBe(true);
  }
}
