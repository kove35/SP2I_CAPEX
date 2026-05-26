/**
 * orchestration-scenarios.mock.js
 * 
 * Données complètes de scénarios d'orchestration pour les tests E2E.
 */

export const DELAY_PROPAGATION_SCENARIO = {
  scenario: {
    id: 'scenario-delay-prop',
    name: 'Delay Propagation Test',
    project_id: 1,
    status: 'ACTIVE',
  },
  initialState: {
    lots: [
      { id: 'facade', name: 'Façade', eta_days: 35, status: 'TO_START', criticality: 0.85 },
      { id: 'menuiserie', name: 'Menuiserie', eta_days: 42, status: 'TO_START', criticality: 0.90 },
      { id: 'peinture', name: 'Peinture', eta_days: 49, status: 'TO_START', criticality: 0.70 },
    ],
    dependencies: [
      { from: 'facade', to: 'menuiserie', type: 'MUST_PRECEDE' },
      { from: 'menuiserie', to: 'peinture', type: 'MUST_PRECEDE' },
    ],
    criticalPath: ['facade', 'menuiserie', 'peinture'],
    criticalPathDuration: 49,
  },
  triggeredChange: {
    type: 'ETA_DELAY',
    lot: 'facade',
    delayDays: 13,  // 35 → 48
  },
  expectedPropagation: {
    menuiserie: { etaBefore: 42, etaAfter: 55 },
    peinture: { etaBefore: 49, etaAfter: 62 },
  },
  expectedWorkflowImpact: {
    execution: { blockedBefore: false, blockedAfter: true },
    planning: { statusChange: 'TO_REVIEW' },
  },
  expectedEvents: [
    'ETA_DELAY_DETECTED',
    'CRITICAL_PATH_RECALCULATED',
    'WORKFLOW_BLOCKED',
    'PLANNING_REFLOW_TRIGGERED',
  ],
};

export const STORAGE_CONFLICT_SCENARIO = {
  scenario: {
    id: 'scenario-storage-conflict',
    name: 'Storage Conflict Test',
    project_id: 1,
    status: 'ACTIVE',
  },
  initialState: {
    storageZones: [
      { zone: 'reception', capacity: 10000, used: 6500, saturation: 0.65 },
      { zone: 'stockage', capacity: 15000, used: 12750, saturation: 0.85 },
    ],
    deliveries: [
      { id: 'del1', lot: 'facade', eta: '2026-03-15', volume: 800 },
      { id: 'del2', lot: 'menuiserie', eta: '2026-04-10', volume: 1200 },
    ],
  },
  triggeredChange: {
    type: 'STORAGE_SATURATION',
    zone: 'stockage',
    saturation: 0.95,  // Crítica - 85% → 95%
  },
  expectedImpact: {
    conflicts: [
      {
        delivery: 'del2',
        conflictType: 'INSUFFICIENT_STORAGE',
        recommendedAction: 'DEFER_DELIVERY',
      },
    ],
  },
  expectedActions: [
    {
      type: 'STORAGE',
      title: 'Résoudre saturation stockage',
      priority: 'CRITICAL',
      recommendations: ['DEFER_DELIVERY', 'SPLIT_DELIVERY'],
    },
  ],
  expectedWorkflows: [
    {
      name: 'delivery',
      statusBefore: 'IN_PROGRESS',
      statusAfter: 'BLOCKED',
      blocker: 'storage_conflict',
    },
  ],
};

export const WORKFLOW_BLOCKING_SCENARIO = {
  scenario: {
    id: 'scenario-workflow-blocking',
    name: 'Workflow Blocking Test',
    project_id: 1,
    status: 'ACTIVE',
  },
  initialState: {
    workflows: [
      {
        id: 'wf_menuiserie',
        name: 'menuiserie',
        status: 'IN_PROGRESS',
        priority: 'HIGH',
        blocked: false,
      },
      {
        id: 'wf_peinture',
        name: 'peinture',
        status: 'TO_DO',
        priority: 'HIGH',
        blocked: false,
        dependsOn: 'menuiserie',
      },
    ],
  },
  triggeredChange: {
    type: 'WORKFLOW_BLOCKING',
    workflow: 'menuiserie',
    reason: 'COMPONENT_UNAVAILABLE',
    blocker: 'menuiserie_delayed',
  },
  expectedPropagation: {
    menuiserie: {
      statusBefore: 'IN_PROGRESS',
      statusAfter: 'BLOCKED',
      blocker: 'menuiserie_delayed',
    },
    peinture: {
      statusBefore: 'TO_DO',
      statusAfter: 'BLOCKED',
      blocker: 'menuiserie_blocked',
    },
  },
  expectedActions: [
    {
      workflow: 'menuiserie',
      actionType: 'RESOLVE_BLOCKER',
      priority: 'CRITICAL',
    },
    {
      workflow: 'peinture',
      actionType: 'WAIT_FOR_DEPENDENCY',
      priority: 'HIGH',
    },
  ],
  expectedEvents: [
    'WORKFLOW_BLOCKING_STARTED',
    'DEPENDENT_WORKFLOW_BLOCKED',
    'BLOCKING_ACTIONS_GENERATED',
  ],
};

export const PLANNING_RECALCULATION_SCENARIO = {
  scenario: {
    id: 'scenario-planning-recalc',
    name: 'Planning Recalculation Test',
    project_id: 1,
    status: 'ACTIVE',
  },
  initialState: {
    planning: {
      startDate: '2026-01-15',
      endDate: '2026-12-31',
      criticality: {
        high: ['facade', 'menuiserie', 'peinture'],
        medium: ['plomberie', 'electricite'],
        low: ['nettoyage'],
      },
    },
    lots: [
      { id: 'facade', eta: 35, criticality: 'HIGH' },
      { id: 'menuiserie', eta: 42, criticality: 'HIGH' },
      { id: 'peinture', eta: 49, criticality: 'HIGH' },
      { id: 'plomberie', eta: 30, criticality: 'MEDIUM' },
      { id: 'electricite', eta: 35, criticality: 'MEDIUM' },
      { id: 'nettoyage', eta: 50, criticality: 'LOW' },
    ],
  },
  triggeredChange: {
    type: 'CRITICAL_LOT_DELAYED',
    lot: 'facade',
    delayDays: 20,
  },
  expectedRecalculation: {
    allLotsRecalculated: true,
    criticalityShift: {
      plomberie: { before: 'MEDIUM', after: 'HIGH' },
      electricite: { before: 'MEDIUM', after: 'HIGH' },
    },
    endDateShift: {
      before: '2026-12-31',
      after: '2027-01-20', // +20 days
    },
  },
  expectedNotifications: [
    { type: 'PLANNING_UPDATED', severity: 'HIGH' },
    { type: 'CRITICALITY_CHANGED', severity: 'WARNING', lot: 'plomberie' },
    { type: 'PROJECT_DELIVERY_DELAYED', severity: 'CRITICAL' },
  ],
};

export const FULL_ORCHESTRATION_SCENARIO = {
  scenario: {
    id: 'scenario-full-orchestration',
    name: 'Full Orchestration Flow',
    project_id: 1,
    status: 'ACTIVE',
  },
  dqe: {
    spatial_units: [
      { building: 'Bâtiment A', level: '1', rooms: 12 },
      { building: 'Bâtiment A', level: '2', rooms: 12 },
    ],
  },
  simulation: {
    scenario_id: 1,
    status: 'COMPLETED',
  },
  procurement: {
    decisions: [
      {
        id: 'pd1',
        status: 'VALIDATED',
        lot: 'facade',
        supplier: 'Supplier A',
      },
      {
        id: 'pd2',
        status: 'ARBITRAGE_IN_PROGRESS',
        lot: 'menuiserie',
        alternatives: 2,
      },
    ],
  },
  execution: {
    actions: [
      {
        id: 'ea1',
        type: 'PROCUREMENT',
        status: 'TO_DO',
        priority: 'CRITICAL',
      },
      {
        id: 'ea2',
        type: 'DELIVERY',
        status: 'TO_DO',
        priority: 'HIGH',
      },
    ],
  },
  spatial: {
    lots: [
      { id: 'facade', x: 100, y: 200, z: 10 },
      { id: 'menuiserie', x: 150, y: 200, z: 15 },
      { id: 'peinture', x: 200, y: 200, z: 20 },
    ],
    storageZones: [
      { zone: 'reception', saturation: 0.7 },
      { zone: 'stockage', saturation: 0.8 },
    ],
  },
  expectedEndState: {
    workflowsActive: 3,
    actionsGenerated: 4,
    eventsDispatched: 8,
    projectStatus: 'EXECUTION_READY',
  },
};
