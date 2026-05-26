/**
 * bim-lite.mock.js
 * 
 * Configuration complète pour un projet BIM-LITE.
 * Utilisée pour les tests de rétrocompatibilité spatial.
 */

export const BIM_LITE_PROJECT = {
  project: {
    id: 1,
    name: 'Test Project BIM-LITE',
    workspace_key: 'sp2i_capex_bim_lite',
    status: 'EXECUTION_READY',
    
    bim_maturity: 'BIM_LITE',
    bim_features_enabled: {
      spatial_timeline: true,
      spatial_dependencies: true,
      storage_heatmap: true,
      risk_propagation_spatial: true,
      workflow_blocking_spatial: false,
      advanced_orchestration: false,
    },
    
    workspace_capabilities: {
      dqe_enabled: true,
      simulation_enabled: true,
      procurement_enabled: true,
      execution_enabled: true,
      spatial_enabled: true,
    },
  },
  
  configuration: {
    ui: {
      tabs: ['overview', 'planning', 'workflow', 'spatial', 'deliveries', 'dependencies'],
      spatial_tab: {
        visible: true,
        components: ['timeline', 'dependencies', 'storage_heatmap', 'risk_panel'],
        layout: 'grid',
      },
    },
    
    orchestration: {
      event_driven: true,
      propagation_enabled: true,
      critical_path_tracking: true,
      storage_conflict_detection: true,
      workflow_blocking: true,
      
      propagation_rules: [
        { source: 'ETA_DELAY', targets: ['CRITICAL_PATH_UPDATE', 'WORKFLOW_UPDATE'] },
        { source: 'STORAGE_SATURATION', targets: ['DELIVERY_CONFLICT', 'STORAGE_ACTION'] },
        { source: 'WORKFLOW_BLOCKING', targets: ['DEPENDENT_BLOCKING', 'ACTION_GENERATED'] },
      ],
    },
    
    spatial: {
      coordinate_system: 'CARTESIAN_3D',
      units: 'meters',
      grid_enabled: true,
      heatmap_zones: ['reception', 'stockage', 'stockage_overflow'],
    },
  },
  
  datasets: {
    dqe_input: {
      type: 'DQE_PARSED',
      spatial_units: 25,
      buildings: 1,
      levels: 2,
      rooms: 24,
    },
    
    simulation_output: {
      scenarios: 1,
      lots: 5,
      dependencies_count: 3,
      critical_path_lots: 3,
      total_duration_days: 49,
    },
    
    procurement_data: {
      decisions: 5,
      status_breakdown: {
        VALIDATED: 3,
        ARBITRAGE_IN_PROGRESS: 1,
        PENDING_APPROVAL: 1,
      },
    },
  },
  
  feature_constraints: {
    // BIM_LITE constraints
    no_advanced_2d_drilldown: true,
    no_3d_model: true,
    no_component_level_tracking: true,
    no_concurrent_zone_analysis: false,
    
    spatial_support: {
      basic_timeline: true,
      basic_dependencies: true,
      basic_storage: true,
      advanced_parallel_zones: false,
      proximity_analysis: false,
    },
  },
  
  expected_behavior: {
    spatial_tab_visible: true,
    storage_heatmap_shows_saturation: true,
    critical_path_highlighted: true,
    workflow_blocking_visual: true,
    event_feed_working: true,
    
    disabled_features: [
      '3d_model_view',
      'component_level_drilldown',
      'concurrent_zone_parallelization',
      'advanced_temporal_analysis',
    ],
  },
};
