/**
 * testDataBuilders.js
 * 
 * Builders pour créer des données de test réalistes.
 */

export function buildSpatialLot(overrides = {}) {
  return {
    id: 'lot_' + Math.random().toString(36).substr(2, 9),
    name: 'Lot exemple',
    eta: 35,
    criticality: 0.7,
    x: Math.random() * 1000,
    y: Math.random() * 1000,
    z: Math.random() * 100,
    storageZone: 'reception',
    status: 'TO_START',
    ...overrides
  };
}

export function buildDependency(from, to, overrides = {}) {
  return {
    from,
    to,
    type: 'MUST_PRECEDE',
    critical: true,
    lagDays: 0,
    ...overrides
  };
}

export function buildWorkflow(name, overrides = {}) {
  return {
    id: 'wf_' + name,
    name,
    status: 'TO_DO',
    priority: 'MEDIUM',
    blocked: false,
    eta: new Date(Date.now() + 30*24*3600*1000).toISOString(),
    actions: [],
    responsibles: [],
    ...overrides
  };
}

export function buildAction(title, overrides = {}) {
  return {
    id: 'action_' + Math.random().toString(36).substr(2, 9),
    title,
    status: 'TO_DO',
    priority: 'MEDIUM',
    dueDate: new Date(Date.now() + 7*24*3600*1000).toISOString(),
    responsible: null,
    ...overrides
  };
}

export function buildEvent(type, overrides = {}) {
  return {
    id: 'event_' + Math.random().toString(36).substr(2, 9),
    type,
    source: 'orchestration_engine',
    timestamp: new Date().toISOString(),
    severity: 'INFO',
    lot: null,
    metadata: {},
    ...overrides
  };
}

export function buildStorageZone(zone, saturation, overrides = {}) {
  return {
    zone,
    saturation,
    capacity: 10000,
    used: saturation * 10000,
    available: (1 - saturation) * 10000,
    conflicts: saturation > 0.8 ? Math.floor(saturation * 5) : 0,
    ...overrides
  };
}

export function buildRiskPropagation(source, target, overrides = {}) {
  return {
    id: 'prop_' + Math.random().toString(36).substr(2, 9),
    source,
    target,
    confidence: 0.8,
    path: [source, target],
    impact: {
      delayDays: 5,
      costImpact: 10000000,
    },
    ...overrides
  };
}

export function buildProject(overrides = {}) {
  return {
    id: 1,
    name: 'Test Project',
    workspace_key: 'test_project',
    status: 'EXECUTION_READY',
    workflow_status: 'EXECUTION_READY',
    dqe_active: true,
    scenario_ready: true,
    procurement_ready: true,
    execution_ready: true,
    ...overrides
  };
}

export function buildFullOrchestrationScenario(overrides = {}) {
  /**
   * Construit un scénario d'orchestration complet pour les tests.
   */
  return {
    project: buildProject(overrides.project),
    spatialSummary: {
      bim_maturity: 'BIM_LITE',
      lots: [
        buildSpatialLot({ id: 'facade', name: 'Façade', eta: 35 }),
        buildSpatialLot({ id: 'menuiserie', name: 'Menuiserie', eta: 42 }),
        buildSpatialLot({ id: 'peinture', name: 'Peinture', eta: 49 }),
      ],
      dependencies: [
        buildDependency('facade', 'menuiserie'),
        buildDependency('menuiserie', 'peinture'),
      ],
      storageZones: [
        buildStorageZone('reception', 0.65),
        buildStorageZone('stockage', 0.85),
      ],
      ...overrides.spatialSummary,
    },
    workflows: [
      buildWorkflow('planning', { status: 'IN_PROGRESS', priority: 'HIGH' }),
      buildWorkflow('procurement', { status: 'BLOCKED', priority: 'CRITICAL', blocker: 'menuiserie_arbitrage' }),
      buildWorkflow('execution', { status: 'TO_DO', priority: 'HIGH' }),
    ],
    events: [
      buildEvent('DQE_IMPORTED'),
      buildEvent('SCENARIO_SIMULATED'),
      buildEvent('PROCUREMENT_ARBITRAGE_STARTED'),
    ],
  };
}
