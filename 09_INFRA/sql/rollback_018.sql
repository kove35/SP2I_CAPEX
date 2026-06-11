-- SP2I CAPEX - Rollback 018 Fact Metre V5.3 Financial
-- Supprime uniquement la vue additive creee par 018_vw_fact_metre_v53_financial.sql.

BEGIN;

DROP VIEW IF EXISTS vw_fact_metre_v53_financial;

COMMIT;
