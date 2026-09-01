/**
 * apiMocks.js
 * 
 * Helpers pour mocker et intercepter les API dans les tests.
 * Utilise page.route() de Playwright.
 */

export async function mockSpatialSummaryApi(page, override = {}) {
  /**
   * Mocker la route de spatial summary.
   */
  await page.route('**/api/projects/*/spatial/summary', route => {
    const response = {
      project_id: 1,
      dqe_id: 'test-dqe',
      bim_maturity: 'BIM_LITE',
      spatial_coverage: {
        batiment: 0.95,
        niveau: 1.0,
        piece: 0.85,
      },
      lots: [
        { id: 'facade', name: 'Façade', eta: 35, criticality: 0.85, x: 100, y: 200, z: 10 },
        { id: 'menuiserie', name: 'Menuiserie', eta: 42, criticality: 0.90, x: 150, y: 200, z: 15 },
        { id: 'peinture', name: 'Peinture', eta: 49, criticality: 0.70, x: 200, y: 200, z: 20 },
      ],
      dependencies: [
        { from: 'facade', to: 'menuiserie', type: 'MUST_PRECEDE' },
        { from: 'menuiserie', to: 'peinture', type: 'MUST_PRECEDE' },
      ],
      storage_zones: [
        { zone: 'reception', saturation: 0.65, capacity: 10000 },
        { zone: 'stockage', saturation: 0.85, capacity: 15000 },
      ],
      ...override
    };
    route.fulfill({ status: 200, body: JSON.stringify(response) });
  });
}

export async function mockTimelineApi(page, override = {}) {
  /**
   * Mocker la timeline spatiale.
   */
  await page.route('**/api/projects/*/spatial/timeline', route => {
    const response = {
      project_id: 1,
      start_date: '2026-01-01',
      end_date: '2026-12-31',
      critical_path: ['facade', 'menuiserie', 'peinture'],
      critical_path_duration: 49,
      slack_time: 5,
      milestones: [
        { date: '2026-03-01', event: 'Démarrage gros œuvre', lots: ['facade'] },
        { date: '2026-05-15', event: 'Menuiserie', lots: ['menuiserie'] },
        { date: '2026-06-30', event: 'Finitions', lots: ['peinture'] },
      ],
      ...override
    };
    route.fulfill({ status: 200, body: JSON.stringify(response) });
  });
}

export async function mockEventFeedApi(page, events = []) {
  /**
   * Mocker l'event feed.
   */
  const defaultEvents = [
    {
      id: '1',
      type: 'DQE_IMPORTED',
      source: 'dqe_engine',
      timestamp: new Date(Date.now() - 1000*60*5).toISOString(),
      severity: 'INFO',
    },
    {
      id: '2',
      type: 'SCENARIO_SIMULATED',
      source: 'simulation_engine',
      timestamp: new Date(Date.now() - 1000*60*3).toISOString(),
      severity: 'INFO',
    },
  ];

  await page.route('**/api/projects/*/events', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        events: events.length > 0 ? events : defaultEvents,
        total: (events || defaultEvents).length,
      })
    });
  });
}

export async function mockStorageHeatmapApi(page, zones = []) {
  /**
   * Mocker la heatmap de stockage.
   */
  const defaultZones = [
    { zone: 'reception', saturation: 0.65, conflicts: 0 },
    { zone: 'stockage_central', saturation: 0.85, conflicts: 2 },
    { zone: 'stockage_overflow', saturation: 0.45, conflicts: 0 },
  ];

  await page.route('**/api/projects/*/spatial/storage-heatmap', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        timestamp: new Date().toISOString(),
        zones: zones.length > 0 ? zones : defaultZones,
      })
    });
  });
}

export async function mockWorkflowsApi(page, workflows = []) {
  /**
   * Mocker les workflows.
   */
  const defaultWorkflows = [
    {
      id: 'wf_planning',
      name: 'planning',
      status: 'IN_PROGRESS',
      priority: 'HIGH',
      blocked: false,
      eta: '2026-06-30',
      actions: [
        { id: 'a1', title: 'Valider planning gros œuvre', status: 'TO_DO', priority: 'CRITICAL' },
      ],
    },
    {
      id: 'wf_procurement',
      name: 'procurement',
      status: 'IN_PROGRESS',
      priority: 'CRITICAL',
      blocked: true,
      blocker: 'menuiserie_arbitrage',
      eta: '2026-05-01',
      actions: [],
    },
    {
      id: 'wf_execution',
      name: 'execution',
      status: 'TO_DO',
      priority: 'HIGH',
      blocked: false,
      eta: '2026-06-15',
      actions: [],
    },
  ];

  await page.route('**/api/projects/*/workflows', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        workflows: workflows.length > 0 ? workflows : defaultWorkflows,
      })
    });
  });
}

export async function mockDependenciesApi(page, dependencies = []) {
  /**
   * Mocker les dépendances.
   */
  const defaultDeps = [
    { from: 'facade', to: 'menuiserie', type: 'MUST_PRECEDE', critical: true },
    { from: 'menuiserie', to: 'peinture', type: 'MUST_PRECEDE', critical: true },
    { from: 'gros_oeuvre', to: 'plomberie', type: 'CAN_OVERLAP', critical: false },
  ];

  await page.route('**/api/projects/*/dependencies', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        dependencies: dependencies.length > 0 ? dependencies : defaultDeps,
      })
    });
  });
}

export async function mockRiskPropagationApi(page, propagations = []) {
  /**
   * Mocker la propagation des risques.
   */
  const defaultProp = [
    {
      id: 'prop1',
      source: 'supplier_risk',
      sourceLevel: 'HIGH',
      target: 'eta_delay',
      confidence: 0.85,
      path: ['supplier_risk', 'eta_delay', 'critical_path_impact'],
    },
    {
      id: 'prop2',
      source: 'storage_saturation',
      sourceLevel: 'MEDIUM',
      target: 'reception_delay',
      confidence: 0.70,
      path: ['storage_saturation', 'reception_delay'],
    },
  ];

  await page.route('**/api/projects/*/risk-propagation', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        propagations: propagations.length > 0 ? propagations : defaultProp,
      })
    });
  });
}

export async function mockProcurementLinesApi(page, rows = []) {
  const defaultRows = [
    {
      id_ligne: 'procurement-line-1',
      designation: 'Luminaire LED import',
      quantite: 120,
      unite: 'U',
      lot: 'Electricite',
      famille: 'Luminaires',
      fournisseur_local: 'Fournisseur local A',
      pays_local: 'Congo-Brazzaville',
      prix_local: 150000,
      fournisseur_chine: 'Fournisseur Chine A',
      port_chine: 'Shanghai',
      fob_chine: 70000,
      landed_cost_chine: 95000,
      gain_net: 6600000,
      roi_import: 0.36,
      risque: 42,
      delai: 48,
      decision_ia: 'IMPORT',
      validation_achat: 'En attente',
    },
    {
      id_ligne: 'procurement-line-2',
      designation: 'Robinetterie import',
      quantite: 80,
      unite: 'U',
      lot: 'Plomberie',
      famille: 'Robinetterie',
      fournisseur_local: 'Fournisseur local B',
      pays_local: 'Congo-Brazzaville',
      prix_local: 125000,
      fournisseur_chine: 'Fournisseur Chine B',
      port_chine: 'Ningbo',
      fob_chine: 58000,
      landed_cost_chine: 82000,
      gain_net: 3440000,
      roi_import: 0.34,
      risque: 48,
      delai: 52,
      decision_ia: 'IMPORT',
      validation_achat: 'En attente',
    },
  ];
  const table = rows.length ? rows : defaultRows;

  await page.route('**/analytics/**', route => {
    const pathname = new URL(route.request().url()).pathname;
    if (!pathname.endsWith('/procurement-lines')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'SUCCESS',
          kpis: {},
          table: [],
          charts: {},
          filters: {},
        }),
      });
    }
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'SUCCESS',
        kpis: {
          nb_lignes: table.length,
          nb_import: table.filter(row => row.decision_ia === 'IMPORT').length,
          nb_hybride: table.filter(row => row.decision_ia === 'HYBRIDE').length,
          gain_net_total: table.reduce((sum, row) => sum + Number(row.gain_net || 0), 0),
          roi_moyen: 0.35,
          risque_moyen: 45,
        },
        table,
      }),
    });
  });
}

export async function mockAllApisForSpatialExecution(page, overrides = {}) {
  /**
   * Mocker toutes les APIs nécessaires pour un test d'exécution spatiale complet.
   */
  await mockSpatialSummaryApi(page, overrides.spatialSummary || {});
  await mockTimelineApi(page, overrides.timeline || {});
  await mockEventFeedApi(page, overrides.events || []);
  await mockStorageHeatmapApi(page, overrides.storageHeatmap || []);
  await mockWorkflowsApi(page, overrides.workflows || []);
  await mockDependenciesApi(page, overrides.dependencies || []);
  await mockRiskPropagationApi(page, overrides.riskPropagation || []);
}

export async function mockApiToReturnError(page, endpoint, statusCode = 500, errorMessage = 'Internal Server Error') {
  /**
   * Mocker une API pour retourner une erreur.
   */
  await page.route(endpoint, route => {
    route.fulfill({
      status: statusCode,
      body: JSON.stringify({ error: errorMessage })
    });
  });
}

export async function mockApiDelay(page, endpoint, delayMs = 2000) {
  /**
   * Mocker une API avec un délai.
   * Utile pour les tests de loading states.
   */
  await page.route(endpoint, async route => {
    await new Promise(resolve => setTimeout(resolve, delayMs));
    route.continue();
  });
}

export async function uninterceptAllApis(page) {
  /**
   * Arrête tous les interceptions d'API.
   */
  await page.unroute('**');
}
