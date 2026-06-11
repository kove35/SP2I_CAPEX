-- SP2I CAPEX - Validation 018 Fact Metre V5.3 Financial
-- Requetes read-only post-migration.

-- 1. Existence de la vue financiere.
SELECT
    'vw_fact_metre_v53_financial' AS relation_name,
    to_regclass('vw_fact_metre_v53_financial') IS NOT NULL AS exists_now;

-- 2. Volumes globaux attendus.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles_uniques,
    COUNT(DISTINCT lot_code) AS nb_lots,
    CASE WHEN COUNT(*) = 4734 THEN 'OK' ELSE 'CHECK_VOLUME' END AS volume_status,
    CASE WHEN COUNT(DISTINCT lot_code) = 18 THEN 'OK' ELSE 'CHECK_LOTS' END AS lot_status
FROM vw_fact_metre_v53_financial;

-- 3. Totaux financiers globaux.
SELECT
    ROUND(SUM(capex_local), 2) AS capex_total_local,
    ROUND(SUM(capex_import), 2) AS capex_total_import,
    ROUND(SUM(capex_optimise), 2) AS capex_total_optimise,
    ROUND(SUM(economie), 2) AS economie_totale,
    ROUND(
        CASE WHEN COALESCE(SUM(capex_local), 0) = 0 THEN 0
             ELSE SUM(economie) / NULLIF(SUM(capex_local), 0)
        END,
        6
    ) AS taux_economie_global
FROM vw_fact_metre_v53_financial;

-- 4. Totaux financiers par lot.
SELECT
    lot_code,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT article_code) AS nb_articles,
    ROUND(SUM(capex_local), 2) AS capex_local,
    ROUND(SUM(capex_import), 2) AS capex_import,
    ROUND(SUM(capex_optimise), 2) AS capex_optimise,
    ROUND(SUM(economie), 2) AS economie
FROM vw_fact_metre_v53_financial
GROUP BY lot_code
ORDER BY lot_code;

-- 5. Articles sans prix.
SELECT
    COUNT(*) FILTER (WHERE prix_local_fcfa <= 0) AS articles_sans_prix_local,
    COUNT(*) FILTER (WHERE prix_import_fcfa <= 0) AS articles_sans_prix_import,
    COUNT(*) FILTER (WHERE prix_optimise_fcfa <= 0) AS articles_sans_prix_optimise
FROM vw_fact_metre_v53_financial;

-- 6. Articles sans lot.
SELECT
    COUNT(*) AS articles_sans_lot
FROM vw_fact_metre_v53_financial
WHERE NULLIF(TRIM(lot_code), '') IS NULL;

-- 7. Couverture de valorisation.
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(*) FILTER (
        WHERE prix_local_fcfa > 0
          AND prix_import_fcfa > 0
          AND prix_optimise_fcfa > 0
          AND capex_local > 0
          AND capex_import > 0
          AND capex_optimise > 0
    ) AS lignes_valorisees,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE prix_local_fcfa > 0
              AND prix_import_fcfa > 0
              AND prix_optimise_fcfa > 0
              AND capex_local > 0
              AND capex_import > 0
              AND capex_optimise > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS couverture_financiere_pct
FROM vw_fact_metre_v53_financial;

-- 8. Lignes non valorisees.
SELECT
    id_ligne,
    lot_code,
    article_code,
    designation,
    quantite,
    prix_local_fcfa,
    prix_import_fcfa,
    prix_optimise_fcfa,
    capex_local,
    capex_import,
    capex_optimise
FROM vw_fact_metre_v53_financial
WHERE prix_local_fcfa <= 0
   OR prix_import_fcfa <= 0
   OR prix_optimise_fcfa <= 0
   OR capex_local <= 0
   OR capex_import <= 0
   OR capex_optimise <= 0
ORDER BY lot_code, article_code
LIMIT 100;

-- 9. Decisions import/local.
SELECT
    decision_import,
    COUNT(*) AS nb_lignes,
    ROUND(SUM(capex_local), 2) AS capex_local,
    ROUND(SUM(capex_import), 2) AS capex_import,
    ROUND(SUM(capex_optimise), 2) AS capex_optimise,
    ROUND(SUM(economie), 2) AS economie
FROM vw_fact_metre_v53_financial
GROUP BY decision_import
ORDER BY decision_import;

-- 10. Tables metiers protegees: lecture de controle uniquement.
SELECT 'fact_metre' AS object_name, COUNT(*) AS current_rows FROM fact_metre
UNION ALL
SELECT 'fact_simulation', COUNT(*) FROM fact_simulation
UNION ALL
SELECT 'fact_approvals', COUNT(*) FROM fact_approvals
UNION ALL
SELECT 'procurement_decisions', COUNT(*) FROM procurement_decisions;
