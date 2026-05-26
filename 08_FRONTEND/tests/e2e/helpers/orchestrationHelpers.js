/**
 * orchestrationHelpers.js
 * 
 * Helpers pour manipuler et tester l'orchestration métier SP2I.
 * Expose les scénarios d'orchestration :
 * - ETA delays
 * - Storage conflicts
 * - Workflow blocking
 * - Planning recalculation
 * - Event propagation
 */

export async function simulateEtaDelay(page, delayDays = 13) {
  /**
   * Simule un retard d'ETA sur un lot critique.
   * Exemple: façade ETA 35j → 48j (+13j)
   * 
   * Déclenche automatiquement :
   * - Recalcul timeline
   * - Update workflow
   * - Propagation critères critiques
   * - Event feed
   */
  await page.evaluate(({ delay }) => {
    // Injecter un événement de changement ETA
    window.dispatchEvent(new CustomEvent('orchestration:eta-changed', {
      detail: {
        type: 'ETA_DELAY',
        lot: 'facade',
        oldEta: 35,
        newEta: 35 + delay,
        delayDays: delay,
        timestamp: new Date().toISOString(),
        propagates: true,
        affectsWorkflow: true,
        priority: 'HIGH',
      }
    }));
  }, { delay: delayDays });

  // Attendre propagation
  await page.waitForTimeout(500);
  await page.waitForLoadState('networkidle');
}

export async function simulateStorageConflict(page, saturationPercent = 85) {
  /**
   * Simule une saturation de stockage site.
   * Déclenche :
   * - Conflit de livraison
   * - Workflow création
   * - Proposition de décalage
   */
  await page.evaluate(({ saturation }) => {
    window.dispatchEvent(new CustomEvent('orchestration:storage-conflict', {
      detail: {
        type: 'STORAGE_SATURATION',
        zone: 'site_reception',
        saturationPercent: saturation,
        capacity: 10000,
        available: 10000 * (1 - saturation/100),
        conflictingDeliveries: [
          { lot: 'menuiserie', volume: 2500, eta: '2026-05-30' },
          { lot: 'plomberie', volume: 1800, eta: '2026-05-30' }
        ],
        suggestedDelay: 3,
        timestamp: new Date().toISOString(),
      }
    }));
  }, { saturation: saturationPercent });

  await page.waitForTimeout(500);
}

export async function blockWorkflow(page, blockReason = 'menuiserie-delayed') {
  /**
   * Bloque un workflow pour simuler une dépendance non respectée.
   * Exemple: menuiserie retardée → peinture bloquée
   */
  await page.evaluate(({ reason }) => {
    window.dispatchEvent(new CustomEvent('orchestration:workflow-blocked', {
      detail: {
        type: 'DEPENDENCY_BLOCKED',
        blockedWorkflow: 'peinture',
        blockingWorkflow: reason,
        blockReason: 'dependent_delay',
        criticality: 'CRITICAL',
        estimatedUnblockDate: new Date(Date.now() + 3*24*3600*1000).toISOString(),
        affectedTeams: ['peinture', 'finitions'],
        timestamp: new Date().toISOString(),
      }
    }));
  }, { reason: blockReason });

  await page.waitForTimeout(500);
}

export async function saturateStorage(page, percentUsed = 85) {
  /**
   * Remplit le stockage à un pourcentage donné.
   * Déclenche alertes si > 70% et critiques si > 80%.
   */
  await page.evaluate(({ percent }) => {
    window.dispatchEvent(new CustomEvent('orchestration:storage-updated', {
      detail: {
        type: 'STORAGE_UPDATE',
        zone: 'site',
        percentUsed: percent,
        criticalThreshold: 80,
        warningThreshold: 70,
        alert: percent >= 70 ? (percent >= 80 ? 'CRITICAL' : 'WARNING') : 'OK',
        timestamp: new Date().toISOString(),
      }
    }));
  }, { percent: percentUsed });

  await page.waitForTimeout(500);
}

export async function triggerRiskPropagation(page, riskSource = 'supplier') {
  /**
   * Déclenche la propagation d'un risque dans l'orchestration.
   * Exemple: risque fournisseur → risque ETA → risque planning
   */
  await page.evaluate(({ source }) => {
    window.dispatchEvent(new CustomEvent('orchestration:risk-propagation', {
      detail: {
        type: 'RISK_PROPAGATION',
        source: source,
        riskLevel: 'HIGH',
        affectedLots: ['menuiserie', 'finitions'],
        affectedWorkflows: ['planning', 'procurement'],
        estimatedImpact: {
          delayDays: 5,
          costImpact: 15000000,
          workflowImpact: ['BLOCKED'],
        },
        propagationChain: [
          { from: source, to: 'eta_planning', confidence: 0.95 },
          { from: 'eta_planning', to: 'critical_path', confidence: 0.87 },
          { from: 'critical_path', to: 'project_delay', confidence: 0.72 },
        ],
        timestamp: new Date().toISOString(),
      }
    }));
  }, { source: riskSource });

  await page.waitForTimeout(500);
}

export async function waitForWorkflowUpdate(page, workflowType = 'planning', timeout = 5000) {
  /**
   * Attend une mise à jour de workflow via event-driven.
   * Valide que la propagation a eu lieu.
   */
  let updateReceived = false;

  const listener = () => { updateReceived = true; };
  await page.evaluate(() => {
    window.__orchestrationTestListener = window.__orchestrationTestListener || {};
    window.__orchestrationTestListener.workflowUpdated = false;
  });

  await page.evaluate(({ type }) => {
    window.__orchestrationTestListener = window.__orchestrationTestListener || {};
    window.addEventListener('orchestration:workflow-updated', () => {
      window.__orchestrationTestListener.workflowUpdated = true;
    });
  }, { type: workflowType });

  // Attendre que le listener détecte la mise à jour
  const startTime = Date.now();
  while (!updateReceived && Date.now() - startTime < timeout) {
    const result = await page.evaluate(() => window.__orchestrationTestListener?.workflowUpdated || false);
    if (result) updateReceived = true;
    else await page.waitForTimeout(100);
  }

  return updateReceived;
}

export async function waitForEventInFeed(page, eventType, timeout = 5000) {
  /**
   * Attend un événement spécifique dans le feed événementiel.
   * Valide la propagation en temps réel.
   */
  try {
    await page.waitForSelector(
      `[data-testid="event-feed-item"][data-event-type="${eventType}"]`,
      { timeout }
    );
    return true;
  } catch {
    return false;
  }
}

export async function getTimelineState(page) {
  /**
   * Récupère l'état actuel de la timeline spatiale.
   * Incluant : dates, dépendances, workflows.
   */
  return await page.evaluate(() => {
    const timeline = document.querySelector('[data-testid="spatial-timeline-board"]');
    if (!timeline) return null;

    return {
      lots: Array.from(document.querySelectorAll('[data-testid^="timeline-lot-"]')).map(el => ({
        id: el.dataset.testid.replace('timeline-lot-', ''),
        name: el.textContent,
        eta: el.dataset.eta,
        status: el.dataset.status,
      })),
      dependencies: Array.from(document.querySelectorAll('[data-testid^="timeline-dep-"]')).map(el => ({
        from: el.dataset.from,
        to: el.dataset.to,
      })),
      criticalPath: document.querySelector('[data-testid="timeline-critical-path"]')?.textContent,
    };
  });
}

export async function getStorageHeatmap(page) {
  return await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid^="heatmap-zone-"], [data-testid="spatial-storage-panel"] article')
    ).map((el) => ({
      zone: el.dataset.zone || el.textContent || "",
      saturation: Number(el.dataset.saturation || 0),
      status: el.dataset.status || "",
    }));
  });
}

export async function getCriticalPathLots(page) {
  /**
   * Récupère les lots du chemin critique.
   */
  return await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid="timeline-lot"][data-critical="true"]')
    ).map(el => el.dataset.testid.replace('timeline-lot-', ''));
  });
}

export async function getWorkflowStatus(page, workflowName) {
  /**
   * Récupère le statut d'un workflow spécifique.
   * Retourne : {status, blocked, priority, actions, eta}
   */
  return await page.evaluate(({ name }) => {
    const workflow = document.querySelector(`[data-testid="workflow-${name}"]`);
    if (!workflow) return null;

    return {
      name: workflow.dataset.name,
      status: workflow.dataset.status,
      blocked: workflow.dataset.blocked === 'true',
      priority: workflow.dataset.priority,
      eta: workflow.dataset.eta,
      actionsCount: workflow.querySelectorAll('[data-testid^="action-"]').length,
    };
  }, { name: workflowName });
}

export async function assertCriticalPathContains(page, expectedLots) {
  /**
   * Assertion métier : chemin critique contient les lots attendus.
   */
  const criticalPath = await getCriticalPathLots(page);
  for (const lot of expectedLots) {
    if (!criticalPath.includes(lot)) {
      throw new Error(`Lot ${lot} attendu dans le chemin critique mais pas trouvé. Chemin: ${criticalPath.join(', ')}`);
    }
  }
  return true;
}

export async function assertWorkflowBlocked(page, workflowName, expectedBlocker) {
  /**
   * Assertion métier : workflow est bloqué par le bon blocant.
   */
  const status = await getWorkflowStatus(page, workflowName);
  if (!status?.blocked) {
    throw new Error(`Workflow ${workflowName} devrait être bloqué mais ne l'est pas`);
  }
  // TODO: vérifier le blocant spécifique quand l'info sera disponible
  return true;
}

export async function assertPropagationChain(page, from, to, expectedLink = true) {
  /**
   * Assertion métier : propagation existe entre deux workflows.
   */
  const propagations = await page.evaluate(({ source, target }) => {
    return Array.from(
      document.querySelectorAll('[data-testid="propagation-link"]')
    ).map(el => ({
      from: el.dataset.from,
      to: el.dataset.to,
    })).filter(p => p.from === source && p.to === target);
  }, { source: from, target: to });

  if ((propagations.length > 0) !== expectedLink) {
    throw new Error(`Propagation ${from}→${to} devrait ${expectedLink ? 'exister' : 'ne pas exister'}`);
  }
  return true;
}
