#!/usr/bin/env psql
-- ============================================================================
-- AUDIT COMPLET : 18 LOTS VS 7 LOTS
-- Requêtes SQL à EXÉCUTER EN LECTURE SEULE
-- ============================================================================
-- ⚠️ LECTURE SEULE : Aucune modification, insertion, suppression ou UPDATE
-- ✅ Exécution sécurisée en production
-- ============================================================================

-- ===========================================================================
-- AUDIT 1 : SOURCES ACTUELLES - fact_metre
-- ===========================================================================
-- Affiche exactement quels lots sont présents dans la table fact_metre
-- C'est LA source du nb_lots = 7 dans /analytics/dashboard

SELECT 
    'fact_metre' AS source,
    COUNT(*) AS total_lignes,
    COUNT(DISTINCT lot) FILTER (WHERE lot IS NOT NULL AND TRIM(CAST(lot AS text)) <> '') AS nb_lots_actifs,
    COUNT(DISTINCT lot) AS nb_lots_avec_null,
    ARRAY_AGG(DISTINCT lot ORDER BY lot) 
        FILTER (WHERE lot IS NOT NULL AND TRIM(CAST(lot AS text)) <> '') 
        AS lots_valides,
    ARRAY_AGG(DISTINCT lot ORDER BY lot) AS lots_all
FROM fact_metre;

-- ===========================================================================
-- AUDIT 2 : VÉRIFIER LES LOTS UNIQUES - Détail par lot
-- ===========================================================================
-- Liste EXACTE des 7 lots avec leur distribution

SELECT 
    COALESCE(NULLIF(TRIM(lot), ''), 'NULL_OU_VIDE') AS lot_code,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_brut_par_lot,
    ROUND(COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_optimise_par_lot,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_par_lot
FROM fact_metre
GROUP BY COALESCE(NULLIF(TRIM(lot), ''), 'NULL_OU_VIDE')
ORDER BY nb_lignes DESC;

-- ===========================================================================
-- AUDIT 3 : VÉRIFIER dim_lot (Référentiel maître des lots)
-- ===========================================================================
-- Montre quels lots sont enregistrés comme "dimension" officielle

SELECT 
    'dim_lot' AS source,
    COUNT(*) AS nb_lots_enregistres,
    ARRAY_AGG(lot ORDER BY lot) AS lots_list
FROM dim_lot;

-- Details par lot
SELECT 
    lot_id,
    lot,
    ordre_lot,
    created_at,
    updated_at
FROM dim_lot
ORDER BY ordre_lot ASC;

-- ===========================================================================
-- AUDIT 4 : VUES GÉNÉRÉES - Building Components
-- ===========================================================================
-- 18 lots générés pour les composants structurels (Gros œuvre, maçonnerie, etc.)

SELECT 
    'vw_sp2i_generated_building' AS source,
    COUNT(DISTINCT lot_code) AS nb_lots_generes,
    COUNT(*) AS total_lignes_generees,
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS lots_list
FROM vw_sp2i_generated_building;

-- Détail par lot généré - Building
SELECT 
    lot_code,
    source_table,
    COUNT(*) AS nb_composants,
    COUNT(DISTINCT component_code) AS nb_composants_uniques,
    ARRAY_AGG(DISTINCT component_code ORDER BY component_code) AS composants
FROM vw_sp2i_generated_building
GROUP BY lot_code, source_table
ORDER BY lot_code;

-- ===========================================================================
-- AUDIT 5 : VUES GÉNÉRÉES - Envelope Components
-- ===========================================================================
-- Façade, menuiserie, toiture

SELECT 
    'vw_sp2i_generated_envelope' AS source,
    COUNT(DISTINCT lot_code) AS nb_lots_generes,
    COUNT(*) AS total_lignes_generees,
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS lots_list
FROM vw_sp2i_generated_envelope;

-- Détail par lot généré - Envelope
SELECT 
    lot_code,
    source_table,
    COUNT(*) AS nb_composants,
    COUNT(DISTINCT component_code) AS nb_composants_uniques,
    ARRAY_AGG(DISTINCT component_code ORDER BY component_code) AS composants
FROM vw_sp2i_generated_envelope
GROUP BY lot_code, source_table
ORDER BY lot_code;

-- ===========================================================================
-- AUDIT 6 : VUES GÉNÉRÉES - Special Systems
-- ===========================================================================
-- Électricité, plomberie, CVC, ascenseurs, sécurité, etc. (systèmes spécialisés)

SELECT 
    'vw_sp2i_generated_special_systems' AS source,
    COUNT(DISTINCT lot_code) AS nb_lots_generes,
    COUNT(*) AS total_lignes_generees,
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS lots_list
FROM vw_sp2i_generated_special_systems;

-- Détail par lot généré - Special Systems (Les vrais "18 lots")
SELECT 
    lot_code,
    source_table,
    COUNT(*) AS nb_composants,
    COUNT(DISTINCT component_code) AS nb_composants_uniques,
    ARRAY_AGG(DISTINCT component_code ORDER BY component_code) AS composants
FROM vw_sp2i_generated_special_systems
GROUP BY lot_code, source_table
ORDER BY lot_code;

-- ===========================================================================
-- AUDIT 7 : UNION TOUS LES LOTS GÉNÉRÉS (18 LOTS COMPLETS)
-- ===========================================================================
-- Consolidation des 18 lots générés depuis tous les vues

SELECT 
    'TOUS_LES_18_LOTS_GENERES' AS source,
    COUNT(DISTINCT lot_code) AS total_lots_generes,
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS complete_lot_list_18
FROM (
    SELECT DISTINCT lot_code FROM vw_sp2i_generated_building
    UNION ALL
    SELECT DISTINCT lot_code FROM vw_sp2i_generated_envelope
    UNION ALL
    SELECT DISTINCT lot_code FROM vw_sp2i_generated_special_systems
) all_lots;

-- ===========================================================================
-- AUDIT 8 : COMPARAISON DIRECTE - 7 vs 18
-- ===========================================================================
-- Affiche en parallèle les 7 lots actuels vs 18 lots attendus

WITH lots_7_actuels AS (
    SELECT 
        lot,
        'ACTUEL_7_LOTS' AS referentiel,
        COUNT(*) AS nb_lignes
    FROM fact_metre
    WHERE lot IS NOT NULL AND TRIM(CAST(lot AS text)) <> ''
    GROUP BY lot
),
lots_18_attendus AS (
    SELECT DISTINCT
        lot_code AS lot,
        'GENERE_18_LOTS' AS referentiel,
        0 AS nb_lignes
    FROM vw_sp2i_generated_building
    UNION ALL
    SELECT DISTINCT
        lot_code,
        'GENERE_18_LOTS',
        0
    FROM vw_sp2i_generated_envelope
    UNION ALL
    SELECT DISTINCT
        lot_code,
        'GENERE_18_LOTS',
        0
    FROM vw_sp2i_generated_special_systems
)
SELECT 
    COALESCE(a.lot, g.lot) AS lot_code,
    a.referentiel AS dans_7_lots_actuels,
    a.nb_lignes AS lignes_dans_fact_metre,
    g.referentiel AS dans_18_lots_generes,
    CASE 
        WHEN a.lot IS NULL THEN '❌ MANQUANT'
        WHEN g.lot IS NULL THEN '⚠️ ORPHELIN'
        ELSE '✅ PRÉSENT'
    END AS statut_integration
FROM lots_7_actuels a
FULL OUTER JOIN lots_18_attendus g ON a.lot = g.lot
ORDER BY COALESCE(a.lot, g.lot);

-- ===========================================================================
-- AUDIT 9 : VÉRIFIER LE CACHE ANALYTICS
-- ===========================================================================
-- Montre comment les métriques sont cachées (source du nb_lots = 7 persistant)

SELECT 
    cache_key,
    dashboard_type,
    created_at,
    expires_at,
    (cached_value::json->>'nb_lots')::INT AS cached_nb_lots
FROM analytics_cache
WHERE cache_key LIKE '%dashboard%'
ORDER BY created_at DESC
LIMIT 10;

-- ===========================================================================
-- AUDIT 10 : VÉRIFIER LES VUES POWERBI ACTUELLES
-- ===========================================================================
-- Affiche si vw_capex_by_lot existe et ce qu'elle contient

-- Test : vw_capex_by_lot existe-t-elle ?
SELECT 
    EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_schema = 'public' 
        AND table_name = 'vw_capex_by_lot'
    ) AS vw_capex_by_lot_exists;

-- Si elle existe, afficher son contenu
SELECT * FROM vw_capex_by_lot
LIMIT 10;

-- Test : vw_capex_summary existe-t-elle ?
SELECT 
    EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_schema = 'public' 
        AND table_name = 'vw_capex_summary'
    ) AS vw_capex_summary_exists;

-- Afficher son contenu
SELECT * FROM vw_capex_summary;

-- ===========================================================================
-- AUDIT 11 : TABLES fact_generation_* - Vérifier leur population
-- ===========================================================================
-- Montre quelles tables de génération contiennent des données

SELECT 
    table_name,
    (xpath('/row/cnt/text()', query_to_xml(format('SELECT COUNT(*) cnt FROM %s', table_name), FALSE, TRUE, '')))[1]::TEXT::INT AS row_count
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'fact_generation_%'
ORDER BY table_name;

-- Détail de chaque table fact_generation_*
SELECT 
    'fact_generation_go' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT lot_code) AS distinct_lots
FROM fact_generation_go
UNION ALL
SELECT 'fact_generation_maconnerie', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_maconnerie
UNION ALL
SELECT 'fact_generation_toiture', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_toiture
UNION ALL
SELECT 'fact_generation_vrd', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_vrd
UNION ALL
SELECT 'fact_generation_facade', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_facade
UNION ALL
SELECT 'fact_generation_menu_ext', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_menu_ext
UNION ALL
SELECT 'fact_generation_menu_int', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_menu_int
UNION ALL
SELECT 'fact_generation_electricite', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_electricite
UNION ALL
SELECT 'fact_generation_plomberie', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_plomberie
UNION ALL
SELECT 'fact_generation_cvc', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_cvc
UNION ALL
SELECT 'fact_generation_ascenseur', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_ascenseur
UNION ALL
SELECT 'fact_generation_incendie', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_incendie
UNION ALL
SELECT 'fact_generation_securite', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_securite
UNION ALL
SELECT 'fact_generation_sanitaires', COUNT(*), COUNT(DISTINCT lot_code) FROM fact_generation_sanitaires
ORDER BY table_name;

-- ===========================================================================
-- AUDIT 12 : SYNTHÈSE FINALE - Nombre de lots par source
-- ===========================================================================
-- Le rapport final : 7 vs 18

SELECT 
    'Source' AS description,
    COUNT(*) FILTER (WHERE source = 'fact_metre') AS nb_lots_from_fact_metre,
    COUNT(*) FILTER (WHERE source = 'dim_lot') AS nb_lots_from_dim_lot,
    COUNT(*) FILTER (WHERE source = 'vw_sp2i_generated_building') AS nb_lots_building,
    COUNT(*) FILTER (WHERE source = 'vw_sp2i_generated_envelope') AS nb_lots_envelope,
    COUNT(*) FILTER (WHERE source = 'vw_sp2i_generated_special_systems') AS nb_lots_special
FROM (
    SELECT 'fact_metre' AS source FROM fact_metre GROUP BY 1
    UNION ALL SELECT 'dim_lot' FROM dim_lot GROUP BY 1
    UNION ALL SELECT 'vw_sp2i_generated_building' FROM vw_sp2i_generated_building GROUP BY 1
    UNION ALL SELECT 'vw_sp2i_generated_envelope' FROM vw_sp2i_generated_envelope GROUP BY 1
    UNION ALL SELECT 'vw_sp2i_generated_special_systems' FROM vw_sp2i_generated_special_systems GROUP BY 1
) sources;

-- ===========================================================================
-- AUDIT 13 : VÉRIFIER QUELS LOTS SONT ORPHELINS
-- ===========================================================================
-- Montre les lots générés qui n'existent PAS dans fact_metre (le problème)

WITH generated_lots AS (
    SELECT DISTINCT lot_code FROM vw_sp2i_generated_building
    UNION ALL SELECT DISTINCT lot_code FROM vw_sp2i_generated_envelope
    UNION ALL SELECT DISTINCT lot_code FROM vw_sp2i_generated_special_systems
)
SELECT 
    g.lot_code,
    CASE 
        WHEN f.lot IS NULL THEN '❌ ORPHELIN - Pas dans fact_metre'
        ELSE '✅ Mappé dans fact_metre'
    END AS statut,
    COUNT(DISTINCT f.id) AS lignes_dans_fact_metre
FROM generated_lots g
LEFT JOIN fact_metre f ON f.lot = g.lot_code OR UPPER(f.lot) = UPPER(g.lot_code)
GROUP BY g.lot_code, f.lot
ORDER BY statut DESC, g.lot_code;

-- ===========================================================================
-- AUDIT 14 : VÉRIFIER LA COHÉRENCE DES VUES POWER BI
-- ===========================================================================
-- Teste que les vues calculent bien à partir de fact_metre

SELECT 
    'vw_capex_summary' AS view_name,
    (SELECT COUNT(*) FROM vw_capex_summary) AS result_rows,
    'Devrait avoir 1 ligne' AS expected
UNION ALL
SELECT 
    'vw_spatial_analytics',
    COUNT(*),
    'Dépend du contenu fact_metre'
FROM vw_spatial_analytics
LIMIT 1;

-- ===========================================================================
-- AUDIT 15 : MÉTRIQUES GLOBALES - Snapshot État système
-- ===========================================================================
-- Résumé complet de l'état du système

SELECT 
    'MÉTRIQUE' AS metriques,
    'VALEUR' AS valeur,
    'COMMENTAIRE' AS commentaire

UNION ALL

SELECT 
    'Lignes fact_metre',
    COUNT(*)::text,
    'Total de lignes dans la table source'
FROM fact_metre

UNION ALL

SELECT 
    'Lots distincts fact_metre',
    COUNT(DISTINCT lot FILTER (WHERE lot IS NOT NULL))::text,
    'Source du nb_lots = 7 dans /analytics/dashboard'
FROM fact_metre

UNION ALL

SELECT 
    'Lots enregistrés dim_lot',
    COUNT(*)::text,
    'Référentiel maître des lots'
FROM dim_lot

UNION ALL

SELECT 
    'Lots générés (union)',
    (
        SELECT COUNT(DISTINCT lot_code)::text FROM (
            SELECT lot_code FROM vw_sp2i_generated_building
            UNION SELECT lot_code FROM vw_sp2i_generated_envelope
            UNION SELECT lot_code FROM vw_sp2i_generated_special_systems
        ) u
    ),
    'Les 18 lots attendus - actuellement orphelins'

UNION ALL

SELECT 
    'Cache analytics entries',
    COUNT(*)::text,
    'Entrées dans le cache - source de persistance du nb_lots=7'
FROM analytics_cache

ORDER BY metriques;

-- ===========================================================================
-- FIN AUDIT - RÉSUMÉ
-- ===========================================================================
-- ✅ Aucune modification, insertion, suppression, UPDATE ou ALTER
-- ✅ Toutes les requêtes sont SELECT seulement
-- ✅ Audit complet en lecture seule
-- ============================================================================
