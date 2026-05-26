/**
 * non-bim.mock.js
 * 
 * Configuration complète pour un projet NON_BIM.
 * Utilisée pour les tests de rétrocompatibilité - sans spatial.
 */

export const NON_BIM_PROJECT = {
  project: {
    id: 3,
    name: 'Test Project NON_BIM',
    workspace_key: 'sp2i_capex_non_bim',
    status: 'EXECUTION_READY',
    
    bim_maturity: 'NON_BIM',
    bim_features_enabled: {
      spatial_timeline: false,
      spatial_dependencies: false,
      storage_heatmap: false,
      risk_propagation_spatial: false,
      workflow_blocking_spatial: false,
      advanced_orchestration: false,
      concurrent_zone_parallelization: false,
    },
    
    workspace_capabilities: {
      dqe_enabled: false,  // DQE pas disponible pour NON_BIM
      simulation_enabled: true,
      procurement_enabled: true,
      execution_enabled: true,
      spatial_enabled: false,
      advanced_spatial: false,
    },
  },
  
  configuration: {
    ui: {
      tabs: ['overview', 'planning', 'workflow', 'deliveries', 'dependencies'],
      spatial_tab: {
        visible: false,
      },
      simplification: {
        removed_components: [
          'spatial_timeline_tab',
          '3d_model_view',
          'storage_heatmap',
          'risk_propagation_visual',
          'spatial_dependencies',
        ],
        hidden_visualizations: [
          'coordinate_display',
          'zone_indicators',
          'heat_colors',
          'spatial_drilldown',
        ],
      },
    },
    
    orchestration: {
      event_driven: true,
      propagation_enabled: true,
      critical_path_tracking: true,
      storage_conflict_detection: false,  // Pas d'infos spatiales
      workflow_blocking: true,
      advanced_propagation: false,
      
      propagation_rules: [
        { source: 'ETA_DELAY', targets: ['CRITICAL_PATH_UPDATE', 'WORKFLOW_UPDATE'] },
        { source: 'WORKFLOW_BLOCKING', targets: ['DEPENDENT_BLOCKING', 'ACTION_GENERATED'] },
      ],
    },
    
    data_sources: {
      input: 'SIMULATION_ONLY',  // Pas de DQE
      output: {
        has_lots: true,
        has_dependencies: true,
        has_spatial_coords: false,
        has_storage_zones: false,
        has_component_data: false,
      },
    },
  },
  
  datasets: {
    dqe_input: null,  // NON_BIM doesn't have DQE
    
    simulation_output: {
      scenarios: 1,
      lots: 5,
      dependencies_count: 3,
      critical_path_lots: 3,
      total_duration_days: 49,
      spatial_data: null,
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
  
  expected_behavior: {
    spatial_tab_hidden: true,
    no_3d_visualization: true,
    no_storage_heatmap: true,
    no_spatial_coordinates: true,
    
    basic_workflows_available: true,
    basic_timeline_available: true,
    critical_path_available: true,
    event_feed_working: true,
    workflow_blocking_working: true,
    
    disabled_features: [
      'spatial_timeline',
      'spatial_dependencies_visualization',
      'storage_heatmap',
      'risk_propagation_spatial',
      'component_drilldown',
      '3d_model_view',
      'concurrent_zone_analysis',
      'proximity_analysis',
    ],
    
    compatible_features: [
      'project_overview',
      'basic_planning',
      'workflow_board',
      'delivery_tracking',
      'dependency_graph_text',
      'event_feed',
      'action_generation',
      'procurement_workflow',
      'critical_path_text',
    ],
  },
  
  regression_testing: {
    // Tests que le système fonctionne sans spatial
    should_work: [
      'project_creation',
      'workflow_creation',
      'action_generation',
      'event_dispatching',
      'workflow_blocking',
      'critical_path_calculation',
      'dependency_propagation',
      'ui_rendering',
    ],
    
    should_not_crash: [
      'missing_spatial_data',
      'null_coordinates',
      'undefined_storage_zones',
      'empty_bim_model',
    ],
    
    performance_baseline: {
      page_load_ms: 2000,
      workflow_update_ms: 500,
      event_propagation_ms: 300,
      ui_render_ms: 1000,
    },
  },
};
