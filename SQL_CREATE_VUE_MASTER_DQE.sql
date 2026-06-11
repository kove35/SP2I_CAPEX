-- ============================================================================
-- CRÉATION : vw_sp2i_generated_dqe_master
-- Vue maître consolidée 18 lots V5.3
-- ============================================================================
-- Mode LECTURE SEULE - SQL à valider avant exécution
-- Statut: PRÊT POUR EXÉCUTION
-- ============================================================================

-- ===========================================================================
-- 1. CRÉER VUE MAÎTRE (Union des 4 sources)
-- ===========================================================================

CREATE OR REPLACE VIEW vw_sp2i_generated_dqe_master AS
SELECT
    -- Identifiant + source
    ROW_NUMBER() OVER (ORDER BY generation_batch, lot_code, article_code, created_at) AS dqe_master_id,
    'QUANTITIES' AS generation_source,
    
    -- Clés métier (OBLIGATOIRES)
    q.lot_code,
    q.generation_batch,
    q.equipment_code AS article_code,
    q.generated_article_code,
    q.generated_designation AS designation,
    q.quantity,
    q.unit,
    
    -- Dimensions spatiales (quantities only)
    q.project_id,
    q.batiment_id,
    q.niveau_id,
    q.appartement,
    q.piece_id,
    q.type_piece,
    
    -- Métadonnées sources (NULL pour quantities)
    NULL::VARCHAR(100) AS source_table,
    NULL::BIGINT AS component_index,
    NULL::VARCHAR(500) AS scope_note,
    
    -- Colonnes spécifiques quantities
    q.source_quantity,
    q.source_surface_m2,
    q.quantity_formula,
    
    q.created_at,
    NOW() AS inserted_at

FROM vw_sp2i_generated_quantities q

UNION ALL

SELECT
    -- Identifiant + source
    ROW_NUMBER() OVER (ORDER BY generation_batch, lot_code, component_code, created_at) + 10000 AS dqe_master_id,
    'BUILDING' AS generation_source,
    
    -- Clés métier
    b.lot_code,
    b.generation_batch,
    b.component_code AS article_code,
    b.generated_article_code,
    b.generated_designation AS designation,
    b.quantity,
    b.unit,
    
    -- Dimensions spatiales (NULL pour building)
    NULL::BIGINT AS project_id,
    NULL::BIGINT AS batiment_id,
    NULL::BIGINT AS niveau_id,
    NULL::VARCHAR(50) AS appartement,
    NULL::BIGINT AS piece_id,
    NULL::VARCHAR(50) AS type_piece,
    
    -- Métadonnées sources
    b.source_table,
    b.component_index,
    b.scope_note,
    
    -- Colonnes spécifiques (NULL)
    NULL::NUMERIC AS source_quantity,
    NULL::NUMERIC AS source_surface_m2,
    NULL::VARCHAR(255) AS quantity_formula,
    
    b.created_at,
    NOW() AS inserted_at

FROM vw_sp2i_generated_building b

UNION ALL

SELECT
    -- Identifiant + source
    ROW_NUMBER() OVER (ORDER BY generation_batch, lot_code, component_code, created_at) + 20000 AS dqe_master_id,
    'ENVELOPE' AS generation_source,
    
    -- Clés métier
    e.lot_code,
    e.generation_batch,
    e.component_code AS article_code,
    e.generated_article_code,
    e.generated_designation AS designation,
    e.quantity,
    e.unit,
    
    -- Dimensions spatiales (NULL pour envelope)
    NULL::BIGINT AS project_id,
    NULL::BIGINT AS batiment_id,
    NULL::BIGINT AS niveau_id,
    NULL::VARCHAR(50) AS appartement,
    NULL::BIGINT AS piece_id,
    NULL::VARCHAR(50) AS type_piece,
    
    -- Métadonnées sources
    e.source_table,
    e.component_index,
    e.scope_note,
    
    -- Colonnes spécifiques (NULL)
    NULL::NUMERIC AS source_quantity,
    NULL::NUMERIC AS source_surface_m2,
    NULL::VARCHAR(255) AS quantity_formula,
    
    e.created_at,
    NOW() AS inserted_at

FROM vw_sp2i_generated_envelope e

UNION ALL

SELECT
    -- Identifiant + source
    ROW_NUMBER() OVER (ORDER BY generation_batch, lot_code, component_code, created_at) + 30000 AS dqe_master_id,
    'SPECIAL' AS generation_source,
    
    -- Clés métier
    s.lot_code,
    s.generation_batch,
    s.component_code AS article_code,
    s.generated_article_code,
    s.generated_designation AS designation,
    s.quantity,
    s.unit,
    
    -- Dimensions spatiales (NULL pour special)
    NULL::BIGINT AS project_id,
    NULL::BIGINT AS batiment_id,
    NULL::BIGINT AS niveau_id,
    NULL::VARCHAR(50) AS appartement,
    NULL::BIGINT AS piece_id,
    NULL::VARCHAR(50) AS type_piece,
    
    -- Métadonnées sources
    s.source_table,
    s.component_index,
    s.scope_note,
    
    -- Colonnes spécifiques (NULL)
    NULL::NUMERIC AS source_quantity,
    NULL::NUMERIC AS source_surface_m2,
    NULL::VARCHAR(255) AS quantity_formula,
    
    s.created_at,
    NOW() AS inserted_at

FROM vw_sp2i_generated_special_systems s

ORDER BY generation_batch, lot_code, article_code, dqe_master_id;

-- ===========================================================================
-- 2. VALIDATION POST-CRÉATION
-- ===========================================================================

/*
Après création de la vue, exécuter:

-- Vérifier la structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'vw_sp2i_generated_dqe_master'
ORDER BY ordinal_position;

-- Compter les lignes par source
SELECT 
    generation_source,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT lot_code) AS distinct_lots,
    COUNT(DISTINCT article_code) AS distinct_articles
FROM vw_sp2i_generated_dqe_master
GROUP BY generation_source
ORDER BY generation_source;

-- Compter total
SELECT 
    'TOTAL_MASTER' AS source,
    COUNT(*) AS nb_lignes_totales,
    COUNT(DISTINCT lot_code) AS distinct_lots_18,
    COUNT(DISTINCT article_code) AS distinct_articles,
    COUNT(DISTINCT generation_batch) AS distinct_batches
FROM vw_sp2i_generated_dqe_master;

-- Vérifier les 18 lots présents
SELECT 
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS lots_dans_master,
    COUNT(DISTINCT lot_code) AS nb_lots_master
FROM vw_sp2i_generated_dqe_master;

-- Vérifier NULL distribution (orphelins acceptables)
SELECT 
    'Colonnes spatiales (quantities only)' AS dimension,
    COUNT(*) FILTER (WHERE project_id IS NULL) AS project_id_nulls,
    COUNT(*) FILTER (WHERE batiment_id IS NULL) AS batiment_id_nulls,
    COUNT(*) FILTER (WHERE niveau_id IS NULL) AS niveau_id_nulls,
    COUNT(*) FILTER (WHERE appartement IS NULL) AS appartement_nulls,
    COUNT(*) FILTER (WHERE piece_id IS NULL) AS piece_id_nulls
FROM vw_sp2i_generated_dqe_master;

SELECT 
    'Métadonnées sources (building/envelope/special only)' AS dimension,
    COUNT(*) FILTER (WHERE source_table IS NULL) AS source_table_nulls,
    COUNT(*) FILTER (WHERE component_index IS NULL) AS component_index_nulls,
    COUNT(*) FILTER (WHERE scope_note IS NULL) AS scope_note_nulls
FROM vw_sp2i_generated_dqe_master;

-- Vérifier NO NULLS dans colonnes obligatoires
SELECT 
    'VALIDATION: Colonnes obligatoires' AS check_type,
    COUNT(*) FILTER (WHERE dqe_master_id IS NULL) AS dqe_master_id_nulls,
    COUNT(*) FILTER (WHERE generation_source IS NULL) AS generation_source_nulls,
    COUNT(*) FILTER (WHERE lot_code IS NULL) AS lot_code_nulls,
    COUNT(*) FILTER (WHERE article_code IS NULL) AS article_code_nulls,
    COUNT(*) FILTER (WHERE designation IS NULL) AS designation_nulls,
    COUNT(*) FILTER (WHERE quantity IS NULL) AS quantity_nulls,
    COUNT(*) FILTER (WHERE unit IS NULL) AS unit_nulls
FROM vw_sp2i_generated_dqe_master;

-- Échantillon par source
SELECT * FROM vw_sp2i_generated_dqe_master 
WHERE generation_source = 'QUANTITIES' LIMIT 5;

SELECT * FROM vw_sp2i_generated_dqe_master 
WHERE generation_source = 'BUILDING' LIMIT 5;

SELECT * FROM vw_sp2i_generated_dqe_master 
WHERE generation_source = 'ENVELOPE' LIMIT 5;

SELECT * FROM vw_sp2i_generated_dqe_master 
WHERE generation_source = 'SPECIAL' LIMIT 5;
*/

-- ===========================================================================
-- 3. INDEX RECOMMANDÉS (après création de la vue)
-- ===========================================================================

/*
Si la vue est matérialisée (CREATE MATERIALIZED VIEW), ajouter:

CREATE INDEX IF NOT EXISTS idx_master_lot_code 
    ON vw_sp2i_generated_dqe_master(lot_code);

CREATE INDEX IF NOT EXISTS idx_master_article_code 
    ON vw_sp2i_generated_dqe_master(article_code);

CREATE INDEX IF NOT EXISTS idx_master_generation_batch 
    ON vw_sp2i_generated_dqe_master(generation_batch);

CREATE INDEX IF NOT EXISTS idx_master_batiment_id 
    ON vw_sp2i_generated_dqe_master(batiment_id) 
    WHERE batiment_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_master_generation_source 
    ON vw_sp2i_generated_dqe_master(generation_source);
*/

-- ===========================================================================
-- 4. EXPORT DQE (À EXÉCUTER APRÈS VALIDATION)
-- ===========================================================================

/*
-- Export CSV (from psql):
\COPY (
    SELECT 
        dqe_master_id,
        lot_code,
        article_code,
        generated_article_code,
        designation,
        quantity,
        unit,
        COALESCE(batiment_id, 'N/A') AS batiment_id,
        COALESCE(niveau_id, 'N/A') AS niveau_id,
        COALESCE(appartement, 'N/A') AS appartement,
        COALESCE(piece_id, 'N/A') AS piece_id,
        COALESCE(source_table, 'N/A') AS source_table,
        generation_source,
        generation_batch,
        created_at
    FROM vw_sp2i_generated_dqe_master
    ORDER BY lot_code, article_code
) TO 'DQE_MPEMBA_V53_18_LOTS_MASTER.csv' WITH CSV HEADER;

-- Excel export (python/pandas):
import pandas as pd

query = '''
SELECT 
    dqe_master_id,
    lot_code,
    article_code,
    generated_article_code,
    designation,
    quantity,
    unit,
    batiment_id,
    niveau_id,
    appartement,
    piece_id,
    source_table,
    generation_source,
    generation_batch,
    created_at
FROM vw_sp2i_generated_dqe_master
ORDER BY lot_code, article_code, dqe_master_id
'''

df = pd.read_sql(query, engine)

# Export Excel
with pd.ExcelWriter('DQE_MPEMBA_V53_18_LOTS_MASTER.xlsx', engine='openpyxl') as writer:
    # Sheet 1: Données complètes
    df.to_excel(writer, sheet_name='DQE_COMPLETE', index=False)
    
    # Sheet 2: Résumé par lot
    summary = df.groupby('lot_code').agg({
        'dqe_master_id': 'count',
        'article_code': 'nunique',
        'quantity': 'sum'
    }).rename(columns={'dqe_master_id': 'nb_lignes', 'article_code': 'nb_articles', 'quantity': 'quantite_totale'})
    summary.to_excel(writer, sheet_name='SUMMARY')
    
    # Sheet 3: Résumé par source
    sources = df.groupby('generation_source').agg({
        'dqe_master_id': 'count',
        'lot_code': 'nunique'
    }).rename(columns={'dqe_master_id': 'nb_lignes', 'lot_code': 'nb_lots'})
    sources.to_excel(writer, sheet_name='SOURCES')
*/

-- ===========================================================================
-- FIN SQL
-- ============================================================================
