/**
 * eventHelpers.js
 * 
 * Helpers pour manipuler les événements et l'event-driven architecture.
 */

export async function getEventFeedFull(page) {
  /**
   * Récupère l'intégralité du feed événementiel.
   */
  return await page.evaluate(() => {
    return Array.from(
      document.querySelectorAll('[data-testid="event-item"]')
    ).map(el => ({
      id: el.dataset.eventId,
      type: el.dataset.eventType,
      source: el.dataset.source,
      lot: el.dataset.lot,
      timestamp: el.dataset.timestamp,
      severity: el.dataset.severity,
      description: el.textContent,
      metadata: JSON.parse(el.dataset.metadata || '{}'),
    })).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  });
}

export async function waitForEventType(page, eventType, timeout = 5000) {
  /**
   * Attend un événement spécifique du type donné.
   */
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const events = await getEventFeedFull(page);
    if (events.some(e => e.type === eventType)) {
      return events.find(e => e.type === eventType);
    }
    await page.waitForTimeout(200);
  }
  throw new Error(`Event type ${eventType} not found within ${timeout}ms`);
}

export async function getEventChain(page, sourceType, targetType, maxHops = 5) {
  /**
   * Récupère la chaîne de propagation des événements.
   * De sourceType jusqu'à targetType en max maxHops événements.
   */
  const events = await getEventFeedFull(page);
  const chain = [];
  let currentType = sourceType;
  let hops = 0;

  while (currentType !== targetType && hops < maxHops) {
    const event = events.find(e => e.type === currentType);
    if (!event) break;
    
    chain.push(event);
    // Trouver l'événement suivant basé sur le metadata
    currentType = event.metadata?.triggeredEvent;
    hops++;
  }

  return {
    found: currentType === targetType,
    chain,
    distance: chain.length,
  };
}

export async function filterEventsBySource(page, source) {
  /**
   * Filtre les événements par source.
   */
  const all = await getEventFeedFull(page);
  return all.filter(e => e.source === source);
}

export async function getEventTimeGaps(page, eventType) {
  /**
   * Calcule les écarts de temps entre événements du même type.
   */
  const events = await getEventFeedFull(page);
  const filtered = events.filter(e => e.type === eventType);
  
  const gaps = [];
  for (let i = 1; i < filtered.length; i++) {
    const gap = new Date(filtered[i-1].timestamp) - new Date(filtered[i].timestamp);
    gaps.push(gap);
  }
  
  return {
    count: filtered.length,
    gaps,
    minGap: Math.min(...gaps),
    maxGap: Math.max(...gaps),
    avgGap: gaps.reduce((a, b) => a + b, 0) / gaps.length,
  };
}

export async function clearEventFeed(page) {
  /**
   * Vide le feed événementiel pour un test propre.
   */
  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent('orchestration:clear-events'));
  });
  await page.waitForTimeout(300);
}

export async function assertEventExists(page, eventType, expectedData = {}) {
  /**
   * Assertion : événement existe avec les données attendues.
   */
  const events = await getEventFeedFull(page);
  const event = events.find(e => {
    if (e.type !== eventType) return false;
    for (const [key, value] of Object.entries(expectedData)) {
      if (event[key] !== value) return false;
    }
    return true;
  });
  
  if (!event) {
    throw new Error(`Event ${eventType} with data ${JSON.stringify(expectedData)} not found`);
  }
  return true;
}

export async function assertEventPropagation(page, sourceType, targetType, expectedHops) {
  /**
   * Assertion : propagation événementielle du source au target en expectedHops.
   */
  const chain = await getEventChain(page, sourceType, targetType);
  if (!chain.found) {
    throw new Error(`No propagation chain found from ${sourceType} to ${targetType}`);
  }
  if (chain.distance !== expectedHops) {
    throw new Error(`Expected ${expectedHops} hops but got ${chain.distance}`);
  }
  return true;
}

export async function assertNoEventOfType(page, eventType) {
  /**
   * Assertion : aucun événement du type donné.
   */
  const events = await getEventFeedFull(page);
  if (events.some(e => e.type === eventType)) {
    throw new Error(`Event type ${eventType} should not exist but found`);
  }
  return true;
}
