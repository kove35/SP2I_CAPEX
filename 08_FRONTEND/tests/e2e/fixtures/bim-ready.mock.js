/**
 * bim-ready.mock.js
 * 
 * Configuration complète pour un projet BIM-READY.
 * Avec toutes les fonctionnalités avancées d'orchestration spatiale.
 */

export const BIM_READY_PROJECT = {
  project: {
    id: 2,
    name: 'Test Project BIM-READY',
    workspace_key: 'sp2i_capex_bim_ready',
    status: 'EXECUTION_READY',
    
    bim_maturity: 'BIM_READY',
    bim_features_enabled: {
      spatial_timeline: true,
      spatial_dependencies: true,
      storage_heatmap: true,
      risk_propagation_spatial: true,
      workflow_blocking_spatial: true,
      advanced_orchestration: true,
      concurrent_zone_parallelization: true,
      "3d_model_view": true,
      component_level_tracking: true,
    },
    
    workspace_capabilities: {
      dqe_enabled: true,
      simulation_enabled: true,
      procurement_enabled: true,
      execution_enabled: true,
      spatial_enabled: true,
      advanced_spatial: true,
    },
  },
  
  configuration: {
    ui: {
      tabs: ['overview', 'planning', 'workflow', 'spatial', '3d_model', 'spatial_advanced', 'deliveries', 'dependencies'],
      spatial_tab: {
        visible: true,
        components: [
          'timeline',
          'dependencies',
          'storage_heatmap',
          'risk_panel',
          '3d_visualization',
          'component_drilldown',
          'temporal_analysis',
          'concurrent_zone_panel',
        ],
        layout: 'advanced_grid',
      },
    },
    
    orchestration: {
      event_driven: true,
      propagation_enabled: true,
      critical_path_tracking: true,
      storage_conflict_detection: true,
      workflow_blocking: true,
      advanced_propagation: true,
      concurrent_zone_orchestration: true,
      proximity_risk_analysis: true,
      
      propagation_rules: [
        { source: 'ETA_DELAY', targets: ['CRITICAL_PATH_UPDATE', 'WORKFLOW_UPDATE', 'ZONE_PARALLELIZATION_IMPACT'] },
        { source: 'STORAGE_SATURATION', targets: ['DELIVERY_CONFLICT', 'STORAGE_ACTION', 'ZONE_CAPACITY_UPDATE'] },
        { source: 'WORKFLOW_BLOCKING', targets: ['DEPENDENT_BLOCKING', 'ACTION_GENERATED', 'ZONE_ACTIVITY_IMPACT'] },
        { source: 'COMPONENT_FAILURE', targets: ['PROXIMITY_RISK', 'ZONE_INFECTION', 'CASCADING_FAILURE'] },
      ],
    },
    
    spatial: {
      coordinate_system: 'CARTESIAN_3D',
      units: 'meters',
      grid_enabled: true,
      grid_snap: 0.1,
      heatmap_zones: ['reception', 'stockage', 'stockage_overflow', 'zone_a', 'zone_b'],
      
      advanced_features: {
        concurrent_zones: [
          { zone_id: 'zone_a', lots: ['facade', 'menuiserie', 'peinture'] },
          { zone_id: 'zone_b', lots: ['plomberie', 'electricite'] },
        ],
        proximity_matrix: true,
        interference_detection: true,
        conflict_resolution: true,
      },
    },
  },
  
  datasets: {
    dqe_input: {
      type: 'DQE_PARSED',
      spatial_units: 150,  // Plus de détails
      buildings: 2,
      levels: 4,
      rooms: 120,
      components: 500,
    },
    
    simulation_output: {
      scenarios: 3,
      lots: 15,
      dependencies_count: 25,
      critical_path_lots: 8,
      total_duration_days: 120,
      parallel_paths: 3,
    },
    
    procurement_data: {
      decisions: 30,
      status_breakdown: {
        VALIDATED: 20,
        ARBITRAGE_IN_PROGRESS: 5,
        PENDING_APPROVAL: 5,
      },
    },
    
    spatial_data: {
      "3d_model_available": true,
      components_mapped: 450,
      proximity_relationships: 120,
      interference_scenarios: 8,
    },
  },
  
  feature_support: {
    spatial_support: {
      basic_timeline: true,
      basic_dependencies: true,
      basic_storage: true,
      advanced_parallel_zones: true,
      proximity_analysis: true,
      interference_detection: true,
      conflict_resolution: true,
      component_level_drilldown: true,
      "3d_visualization": true,
      temporal_analysis: true,
    },
    
    orchestration_support: {
      basic_event_propagation: true,
      advanced_propagation: true,
      proximity_risk: true,
      cascading_failure: true,
      zone_interference: true,
      component_failure_simulation: true,
    },
  },
  
  advanced_features: {
    concurrent_zone_orchestration: {
      enabled: true,
      zones: [
        {
          id: 'zone_a',
          name: 'Façade et finitions',
          lots: ['facade', 'menuiserie', 'peinture'],
          can_parallelize: true,
          parallelizes_with: ['zone_b'],
        },
        {
          id: 'zone_b',
          name: 'Réseaux',
          lots: ['plomberie', 'electricite'],
          can_parallelize: true,
          parallelizes_with: ['zone_a'],
        },
      ],
    },
    
    component_failure_simulation: {
      enabled: true,
      failure_types: ['UNAVAILABLE', 'DELAYED', 'WRONG_SPEC', 'QUALITY_ISSUE'],
      propagation_radius: 50,  // meters
      confidence_scoring: true,
    },
    
    temporal_analysis: {
      enabled: true,
      supports: ['timeline_view', 'gantt_advanced', 'critical_chain', 'buffer_analysis'],
    },
  },
  
  expected_behavior: {
    all_spatial_features_visible: true,
    advanced_orchestration_working: true,
    concurrent_zones_functional: true,
    component_drilldown_available: true,
    "3d_model_rendering": true,
    proximity_analysis_working: true,
    
    enabled_features: [
      'spatial_timeline',
      'spatial_dependencies',
      'storage_heatmap',
      'risk_propagation_spatial',
      'workflow_blocking_spatial',
      'concurrent_zone_parallelization',
      'component_level_tracking',
      '3d_model_view',
      'advanced_temporal_analysis',
      'proximity_risk_analysis',
      'cascading_failure_simulation',
    ],
  },
};
