-- Every query must return zero rows, except the final reconciliation report.

SELECT 'missing_project' AS failure, id_ligne
FROM vw_fact_metre_financial_v6
WHERE projet_id IS NULL OR NULLIF(TRIM(project_code), '') IS NULL;

SELECT 'duplicate_project_line' AS failure, projet_id, canonical_id_ligne, COUNT(*)
FROM vw_fact_metre_financial_v6
GROUP BY projet_id, canonical_id_ligne
HAVING COUNT(*) <> 1;

SELECT 'incomplete_price' AS failure, id_ligne
FROM vw_fact_metre_financial_v6
WHERE prix_local_fcfa IS NULL OR prix_import_fcfa IS NULL OR prix_optimise_fcfa IS NULL;

WITH fact AS (
    SELECT projet_id, SUM(capex_local) AS brut, SUM(capex_optimise) AS optimise, SUM(economie) AS economie
    FROM vw_fact_metre_financial_v6 GROUP BY projet_id
)
SELECT 'summary_mismatch' AS failure, f.projet_id
FROM fact f
JOIN vw_project_cost_summary_v6 s USING (projet_id)
WHERE ROUND(f.brut, 2) <> ROUND(s.capex_direct, 2)
   OR ROUND(f.optimise, 2) <> ROUND(s.capex_optimise, 2)
   OR ROUND(f.economie, 2) <> ROUND(s.economie_nette, 2);

WITH direction AS (
    SELECT projet_id, SUM(capex_direct) AS brut
    FROM vw_dashboard_direction_v6_scoped GROUP BY projet_id
)
SELECT 'direction_mismatch' AS failure, d.projet_id
FROM direction d
JOIN vw_project_cost_summary_v6 s USING (projet_id)
WHERE ROUND(d.brut, 2) <> ROUND(s.capex_direct, 2);

SELECT
    project_code,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT lot) AS nb_lots,
    ROUND(SUM(capex_local), 2) AS capex_brut,
    ROUND(SUM(capex_optimise), 2) AS capex_optimise,
    ROUND(SUM(economie), 2) AS economie
FROM vw_fact_metre_financial_v6
GROUP BY project_code
ORDER BY project_code;
