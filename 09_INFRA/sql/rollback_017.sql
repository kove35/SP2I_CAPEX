-- SP2I CAPEX - Rollback 017 Pricing Strategy BPU V5.3
-- Supprime uniquement les objets additifs crees par 017_bpu_v53_pricing_strategy.sql.

BEGIN;

DROP VIEW IF EXISTS vw_bpu_v53_priced;

DROP TABLE IF EXISTS dim_pricing_strategy_v53;

COMMIT;
