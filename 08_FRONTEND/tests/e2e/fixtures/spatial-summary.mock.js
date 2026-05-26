/**
 * spatial-summary.mock.js
 * 
 * Mock data complet pour la spatial summary.
 * Utilisée pour les tests de timeline, dépendances, heatmap.
 */

export const SPATIAL_SUMMARY_BIM_LITE = {
  project_id: 1,
  dqe_id: 'DQE_2026_001',
  workspace_key: 'sp2i_capex_test',
  bim_maturity: 'BIM_LITE',
  timestamp: '2026-01-15T10:00:00Z',
  
  spatial_coverage: {
    batiment: 0.95,
    niveau: 1.0,
    piece: 0.85,
  },
  
  lots: [
    {
      id: 'facade',
      name: 'Façade bâtiment A',
      description: 'Nettoyage et traitement façade',
      eta_days: 35,
      criticality_score: 0.85,
      status: 'TO_START',
      responsible: null,
      x: 100,
      y: 200,
      z: 10,
      zone: 'zone_a',
      storage_zone: 'reception',
      area_m2: 450,
      volume_m3: 0,
    },
    {
      id: 'menuiserie',
      name: 'Menuiserie extérieure',
      description: 'Installation fenêtres et portes',
      eta_days: 42,
      criticality_score: 0.90,
      status: 'TO_START',
      responsible: null,
      x: 150,
      y: 200,
      z: 15,
      zone: 'zone_a',
      storage_zone: 'stockage',
      area_m2: 150,
      volume_m3: 20,
      depends_on: ['facade'],
    },
    {
      id: 'peinture',
      name: 'Peinture intérieure',
      description: 'Peinture murs et plafonds',
      eta_days: 49,
      criticality_score: 0.70,
      status: 'TO_START',
      responsible: null,
      x: 200,
      y: 200,
      z: 20,
      zone: 'zone_a',
      storage_zone: 'stockage',
      area_m2: 2000,
      volume_m3: 0,
      depends_on: ['menuiserie'],
    },
    {
      id: 'plomberie',
      name: 'Installation plomberie',
      description: 'Tuyauterie et sanitaires',
      eta_days: 30,
      criticality_score: 0.60,
      status: 'TO_START',
      responsible: null,
      x: 100,
      y: 100,
      z: 5,
      zone: 'zone_b',
      storage_zone: 'reception',
      area_m2: 0,
      volume_m3: 50,
    },
    {
      id: 'electricite',
      name: 'Installation électricité',
      description: 'Câblage électrique',
      eta_days: 35,
      criticality_score: 0.65,
      status: 'TO_START',
      responsible: null,
      x: 150,
      y: 100,
      z: 5,
      zone: 'zone_b',
      storage_zone: 'reception',
      area_m2: 0,
      volume_m3: 0,
    },
  ],
  
  dependencies: [
    { from: 'facade', to: 'menuiserie', type: 'MUST_PRECEDE', lag_days: 0, critical: true },
    { from: 'menuiserie', to: 'peinture', type: 'MUST_PRECEDE', lag_days: 0, critical: true },
    { from: 'plomberie', to: 'electricite', type: 'CAN_OVERLAP', lag_days: 0, critical: false },
  ],
  
  critical_path: {
    lots: ['facade', 'menuiserie', 'peinture'],
    duration_days: 49,
    slack_time_days: 5,
    start_date: '2026-01-15',
    end_date: '2026-03-05',
  },
  
  storage_zones: [
    {
      zone: 'reception',
      name: 'Zone de réception',
      capacity_m3: 10000,
      used_m3: 6500,
      saturation: 0.65,
      conflicts: 0,
      alert_level: 'OK',
    },
    {
      zone: 'stockage',
      name: 'Zone de stockage central',
      capacity_m3: 15000,
      used_m3: 12750,
      saturation: 0.85,
      conflicts: 2,
      alert_level: 'WARNING',
    },
    {
      zone: 'stockage_overflow',
      name: 'Zone débordement',
      capacity_m3: 5000,
      used_m3: 2250,
      saturation: 0.45,
      conflicts: 0,
      alert_level: 'OK',
    },
  ],
  
  risk_propagation: [
    {
      id: 'prop1',
      source: 'supplier_delay_menuiserie',
      source_level: 'HIGH',
      target: 'eta_delay_peinture',
      confidence: 0.85,
      path: ['supplier_delay_menuiserie', 'eta_delay_menuiserie', 'eta_delay_peinture'],
      impact_days: 7,
      cost_impact_eur: 15000,
    },
    {
      id: 'prop2',
      source: 'storage_saturation',
      source_level: 'MEDIUM',
      target: 'delivery_delay',
      confidence: 0.70,
      path: ['storage_saturation', 'delivery_conflict', 'delivery_delay'],
      impact_days: 3,
      cost_impact_eur: 5000,
    },
  ],
  
  workflows: [
    {
      id: 'wf_planning',
      name: 'Planning',
      status: 'IN_PROGRESS',
      priority: 'HIGH',
      blocked: false,
      eta: '2026-03-05',
      actions: [
        { id: 'a1', title: 'Valider planning détaillé', status: 'TO_DO', priority: 'CRITICAL' },
      ],
      responsible: null,
    },
    {
      id: 'wf_procurement',
      name: 'Procurement',
      status: 'IN_PROGRESS',
      priority: 'CRITICAL',
      blocked: true,
      blocker: 'menuiserie_arbitrage',
      eta: '2026-02-01',
      actions: [
        { id: 'a2', title: 'Arbitrage menuiserie', status: 'IN_PROGRESS', priority: 'CRITICAL' },
        { id: 'a3', title: 'Valider fournisseurs', status: 'TO_DO', priority: 'HIGH' },
      ],
      responsible: 'achats@company.com',
    },
    {
      id: 'wf_execution',
      name: 'Execution',
      status: 'TO_DO',
      priority: 'HIGH',
      blocked: false,
      eta: '2026-03-15',
      actions: [],
      responsible: null,
    },
  ],
  
  metrics: {
    total_duration_days: 49,
    slack_time_days: 5,
    lots_count: 5,
    critical_lots: 3,
    storage_utilization: 0.73,
    workflow_status: 'PARTIALLY_BLOCKED',
    readiness_score: 0.65,
  },
};

export const SPATIAL_SUMMARY_BIM_READY = {
  ...SPATIAL_SUMMARY_BIM_LITE,
  bim_maturity: 'BIM_READY',
  
  advanced_spatial: {
    3d_model_url: 'https://bim-server/model/project-1',
    building_hierarchies: [
      {
        id: 'bath_a',
        name: 'Bâtiment A',
        levels: [
          { id: 'level_1', name: 'RDC', area_m2: 1200 },
          { id: 'level_2', name: 'Etage 1', area_m2: 1200 },
        ],
      },
    ],
    lot_spatial_relationships: [
      { lot: 'facade', building: 'bath_a', levels: ['level_1', 'level_2'] },
      { lot: 'menuiserie', building: 'bath_a', levels: ['level_1', 'level_2'] },
    ],
    proximity_analysis: [
      { lot1: 'facade', lot2: 'menuiserie', distance_m: 15, interference: false },
    ],
  },
  
  advanced_orchestration: {
    parallel_execution_zones: [
      {
        zone_id: 'zone_a',
        lots: ['facade', 'menuiserie', 'peinture'],
        can_parallelize_with: ['zone_b'],
      },
      {
        zone_id: 'zone_b',
        lots: ['plomberie', 'electricite'],
        can_parallelize_with: ['zone_a'],
      },
    ],
  },
};
