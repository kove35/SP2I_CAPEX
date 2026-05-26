/**
 * spatialHelpers.js
 * 
 * Helpers pour tester la spatial intelligence et orchestration spatiale.
 * Manipule :
 * - Timeline spatiale
 * - Dépendances spatiales
 * - Heatmaps de stockage
 * - Événements spatiaux
 * - Critical path spatial
 */

export async function openSpatialTab(page) {
  /**
   * Navigue vers l'onglet spatial si disponible.
   * Vérifie que le BIM maturity le supporte.
   */
  const spatialTab = page.getByTestId("execution-tab-spatial");
  await expect(spatialTab).toBeVisible();
  await spatialTab.click();
  await page.waitForLoadState('networkidle');
}

export async function expectSpatialTabVisible(page) {
  /**
   * Assertion que l'onglet spatial est visible.
   * Indique BIM_LITE ou BIM_READY.
   */
  const tab = page.getByTestId("execution-tab-spatial");
  return await tab.isVisible();
}

export async function getSpatialTimelineState(page) {
  /**
   * Récupère l'état complet de la timeline spatiale.
   * Retourne : lots, dépendances, coordonnées, heatmap, risques.
   */
  return await page.evaluate(() => {
    const timeline = document.querySelector('[data-testid="spatial-timeline-board"]');
    if (!timeline) return null;

    return {
      lots: Array.from(document.querySelectorAll('[data-testid^="spatial-lot-"]')).map(el => ({
        id: el.dataset.lotId,
        name: el.textContent,
        x: el.dataset.x,
        y: el.dataset.y,
        z: el.dataset.z,
        eta: el.dataset.eta,
        criticality: el.dataset.criticality,
        storageZone: el.dataset.storageZone,
        color: window.getComputedStyle(el).backgroundColor,
      })),
      dependencies: Array.from(document.querySelectorAll('[data-testid^="spatial-dep-"]')).map(el => ({
        from: el.dataset.from,
        to: el.dataset.to,
        type: el.dataset.type,
      })),
      heatmap: {
        zones: Array.from(document.querySelectorAll('[data-testid="heatmap-zone"]')).map(el => ({
          zone: el.dataset.zone,
          saturation: parseFloat(el.dataset.saturation),
          color: window.getComputedStyle(el).backgroundColor,
        })),
      },
      events: Array.from(document.querySelectorAll('[data-testid="spatial-event"]')).map(el => ({
        type: el.dataset.eventType,
        lot: el.dataset.lot,
        timestamp: el.dataset.timestamp,
      })),
    };
  });
}

export async function drilldownLot(page, lotId) {
  /**
   * Drille down sur un lot spécifique pour voir les détails.
   * Affiche détails, dépendances, impacts.
   */
  const drilldownPanel = page.getByTestId("spatial-drilldown-panel");
  const lotElement = page.getByTestId(`spatial-lot-${lotId}`);
  
  await lotElement.click();
  await page.waitForLoadState('networkidle');
  
  return {
    visible: await drilldownPanel.isVisible(),
    lotId: await drilldownPanel.evaluate(el => el.dataset.lotId),
    title: await drilldownPanel.getByTestId("drilldown-title").textContent(),
    dependencies: await page.evaluate(() => {
      return Array.from(
        document.querySelectorAll('[data-testid="drilldown-dependency"]')
      ).map(el => el.textContent);
    }),
  };
}

export async function getSpatialDependencies(page) {
  /**
   * Récupère toutes les dépendances spatiales visualisées.
   * Format : [{from, to, type, critical}]
   */
  return await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid="spatial-dependency"]')
    ).map(el => ({
      from: el.dataset.from,
      to: el.dataset.to,
      type: el.dataset.type,
      critical: el.dataset.critical === 'true',
      visualized: window.getComputedStyle(el).display !== 'none',
    }));
  });
}

export async function getStorageHeatmap(page) {
  /**
   * Récupère l'heatmap de stockage.
   * Retourne zones et taux de saturation.
   */
  return await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid="heatmap-zone"]')
    ).map(el => ({
      zone: el.dataset.zone,
      saturation: parseFloat(el.dataset.saturation),
      conflictCount: parseInt(el.dataset.conflicts || 0),
      color: window.getComputedStyle(el).backgroundColor,
      alert: el.dataset.saturation >= 80 ? 'CRITICAL' : 
             el.dataset.saturation >= 70 ? 'WARNING' : 'OK',
    }));
  });
}

export async function getRiskPropagationPanel(page) {
  /**
   * Récupère le panneau de propagation des risques.
   * Retourne la chaîne de propagation visuelle.
   */
  return await page.evaluate(() => {
    const panel = document.querySelector('[data-testid="spatial-risk-propagation-panel"]');
    if (!panel) return null;

    return {
      risks: Array.from(
        panel.querySelectorAll('[data-testid="risk-node"]')
      ).map(el => ({
        source: el.dataset.source,
        level: el.dataset.level,
        confidence: parseFloat(el.dataset.confidence),
      })),
      propagations: Array.from(
        panel.querySelectorAll('[data-testid="propagation-link"]')
      ).map(el => ({
        from: el.dataset.from,
        to: el.dataset.to,
        confidence: parseFloat(el.dataset.confidence),
      })),
    };
  });
}

export async function getCriticalPathSpatial(page) {
  /**
   * Récupère le chemin critique visualisé spatialement.
   */
  return await page.evaluate(() => {
    const path = document.querySelector('[data-testid="spatial-critical-path"]');
    if (!path) return null;

    return {
      lots: Array.from(
        path.querySelectorAll('[data-testid="critical-lot"]')
      ).map(el => el.dataset.lotId),
      duration: path.dataset.duration,
      slackTime: path.dataset.slackTime,
      visualization: {
        color: window.getComputedStyle(path).stroke,
        width: window.getComputedStyle(path).strokeWidth,
      },
    };
  });
}

export async function getEventFeed(page) {
  /**
   * Récupère l'event feed spatial avec les événements récents.
   */
  return await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid="spatial-event-item"]')
    ).map(el => ({
      type: el.dataset.eventType,
      lot: el.dataset.lot,
      timestamp: el.dataset.timestamp,
      description: el.textContent,
      severity: el.dataset.severity,
    })).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  });
}

export async function assertSpatialLotCritical(page, lotId) {
  /**
   * Assertion : lot est marqué comme critique dans la vue spatiale.
   */
  const lot = page.getByTestId(`spatial-lot-${lotId}`);
  const criticality = await lot.getAttribute('data-criticality');
  if (criticality !== 'CRITICAL') {
    throw new Error(`Lot ${lotId} devrait être CRITICAL mais est ${criticality}`);
  }
  return true;
}

export async function assertStorageSaturated(page, zoneId, expectedSaturation = 85) {
  /**
   * Assertion : zone de stockage saturée au pourcentage attendu.
   */
  const heatmap = await getStorageHeatmap(page);
  const zone = heatmap.find(z => z.zone === zoneId);
  if (!zone) throw new Error(`Zone ${zoneId} not found in heatmap`);
  if (Math.abs(zone.saturation - expectedSaturation) > 5) {
    throw new Error(`Zone ${zoneId} saturation ${zone.saturation}% != ${expectedSaturation}%`);
  }
  return true;
}

export async function assertDependencyExists(page, fromLot, toLot) {
  /**
   * Assertion : dépendance spatiale existe.
   */
  const deps = await getSpatialDependencies(page);
  const dep = deps.find(d => d.from === fromLot && d.to === toLot);
  if (!dep) {
    throw new Error(`Dépendance ${fromLot}→${toLot} non trouvée`);
  }
  return true;
}

export async function assertCriticalPathContainsSpatial(page, expectedLots) {
  /**
   * Assertion : chemin critique spatial contient les lots attendus.
   */
  const path = await getCriticalPathSpatial(page);
  if (!path) throw new Error('Aucun chemin critique trouvé');
  
  for (const lot of expectedLots) {
    if (!path.lots.includes(lot)) {
      throw new Error(`Lot ${lot} attendu dans chemin critique spatial mais pas trouvé. Chemin: ${path.lots.join(',')}`);
    }
  }
  return true;
}

export async function assertRiskPropagates(page, from, to) {
  /**
   * Assertion : risque se propage de 'from' vers 'to'.
   */
  const panel = await getRiskPropagationPanel(page);
  if (!panel) throw new Error('Aucun panneau de propagation trouvé');
  
  const prop = panel.propagations.find(p => p.from === from && p.to === to);
  if (!prop) {
    throw new Error(`Propagation ${from}→${to} non trouvée`);
  }
  return true;
}

export async function assertEventInFeed(page, eventType, lotId) {
  /**
   * Assertion : événement spécifique visible dans le feed spatial.
   */
  const events = await getEventFeed(page);
  const event = events.find(e => e.type === eventType && e.lot === lotId);
  if (!event) {
    throw new Error(`Événement ${eventType} pour lot ${lotId} non trouvé dans feed`);
  }
  return true;
}
