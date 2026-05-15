/*
SP2I CAPEX - Diagnostics pipeline et Power BI

Ces requetes ne modifient aucune donnee. Elles servent a verifier qu'un import
Excel/DQE n'a pas perdu de lignes, de lots ou de cles dimensionnelles.
*/

/* 1. Lots presents dans la table de faits. */
SELECT
    lot,
    COUNT(*) AS lignes,
    ROUND(SUM(capex_local)::NUMERIC, 2) AS capex_local
FROM fact_metre
GROUP BY lot
ORDER BY COALESCE(NULLIF(regexp_replace(lot, '\D', '', 'g'), '')::INTEGER, 999), lot;

/* 2. Lignes sans lot ou sans relation dimensionnelle. */
SELECT
    COUNT(*) FILTER (WHERE lot IS NULL OR trim(lot) = '') AS lignes_sans_lot,
    COUNT(*) FILTER (WHERE lot_id IS NULL) AS lignes_sans_lot_id,
    COUNT(*) FILTER (WHERE famille_id IS NULL) AS lignes_sans_famille_id,
    COUNT(*) FILTER (WHERE niveau_id IS NULL) AS lignes_sans_niveau_id,
    COUNT(*) FILTER (WHERE batiment_id IS NULL) AS lignes_sans_batiment_id,
    COUNT(*) AS lignes_total
FROM fact_metre;

/* 3. Dimensions orphelines visibles comme slicers vides dans Power BI. */
SELECT 'dim_lot' AS dimension, lot AS valeur
FROM dim_lot d
WHERE NOT EXISTS (SELECT 1 FROM fact_metre f WHERE f.lot_id = d.lot_id)
UNION ALL
SELECT 'dim_famille', famille
FROM dim_famille d
WHERE NOT EXISTS (SELECT 1 FROM fact_metre f WHERE f.famille_id = d.famille_id)
UNION ALL
SELECT 'dim_niveau', niveau
FROM dim_niveau d
WHERE NOT EXISTS (SELECT 1 FROM fact_metre f WHERE f.niveau_id = d.niveau_id)
UNION ALL
SELECT 'dim_batiment', batiment
FROM dim_batiment d
WHERE NOT EXISTS (SELECT 1 FROM fact_metre f WHERE f.batiment_id = d.batiment_id);

/* 4. Controle des KPI pre-calcules. */
SELECT * FROM v_kpi_capex;

/* 5. Qualite DQE par statut. */
SELECT * FROM v_qualite_dqe ORDER BY nombre_lignes DESC;

/* 6. Repartition IMPORT / LOCAL. */
SELECT * FROM v_kpi_import_local ORDER BY decision_import;
