-- SP2I CAPEX - Phase 031 rollback
-- Conservative rollback: removes only V6 parallel views.
-- V5 views and canonical financial views are preserved.

BEGIN;

DROP VIEW IF EXISTS vw_cost_intelligence_v6;
DROP VIEW IF EXISTS vw_dashboard_direction_v6;
DROP VIEW IF EXISTS vw_project_cost_summary;
DROP VIEW IF EXISTS vw_bpu_v53_priced_v2;

-- dim_price_reference and dim_article_price_mapping are intentionally kept.
-- They are additive reference tables and may already be used by Phase 029B.
-- If a full cleanup is required after manual approval, remove only rows where:
--   source_prix = 'SP2I_V6_BUDGETARY_REFERENCE'
--   mapping_source = 'AUTO_RULE_031'

COMMIT;

-- Post-rollback validation:
-- SELECT to_regclass('vw_bpu_v53_priced_v2');
-- SELECT to_regclass('vw_project_cost_summary');
-- SELECT to_regclass('vw_dashboard_direction_v6');
-- SELECT to_regclass('vw_cost_intelligence_v6');
-- SELECT to_regclass('vw_bpu_v53_priced');
-- SELECT to_regclass('vw_fact_metre_current');
-- SELECT to_regclass('vw_fact_metre_financial_canonical');
