-- ============================================================================
-- AUDIT : SCHÉMA DES 4 VUES GÉNÉRÉES V5.3
-- MODE LECTURE SEULE - Aucune modification
-- ============================================================================

/*
Objectif: Analyser la structure des 4 vues pour créer vw_sp2i_generated_dqe_master

Vues à auditer:
1. vw_sp2i_generated_quantities      (V5.2.1 - Équipements avec quantités)
2. vw_sp2i_generated_building        (V5.3 - Gros œuvre, maçonnerie, toiture, VRD)
3. vw_sp2i_generated_envelope        (V5.3 - Façade, menuiseries)
4. vw_sp2i_generated_special_systems (V5.3 - Ascenseurs, incendie, sécurité, etc.)

Question: Quel schéma unifier ?
*/

-- ===========================================================================
-- AUDIT 1 : Structure vw_sp2i_generated_quantities
-- ===========================================================================

SELECT 
    'vw_sp2i_generated_quantities' AS view_name,
    column_name,
    ordinal_position,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'vw_sp2i_generated_quantities'
ORDER BY ordinal_position;

-- Échantillon de données
SELECT 
    'vw_sp2i_generated_quantities' AS source,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT lot_code) AS distinct_lots,
    COUNT(DISTINCT generation_batch) AS distinct_batches,
    COUNT(DISTINCT project_id) AS distinct_projects,
    COUNT(DISTINCT batiment_id) AS distinct_batiments,
    COUNT(DISTINCT niveau_id) AS distinct_niveaux,
    COUNT(DISTINCT appartement) AS distinct_appartements,
    COUNT(DISTINCT piece_id) AS distinct_pieces,
    COUNT(DISTINCT equipment_code) AS distinct_equipments
FROM vw_sp2i_generated_quantities;

-- Colonnes détail
SELECT * FROM vw_sp2i_generated_quantities LIMIT 5;

-- ===========================================================================
-- AUDIT 2 : Structure vw_sp2i_generated_building
-- ===========================================================================

SELECT 
    'vw_sp2i_generated_building' AS view_name,
    column_name,
    ordinal_position,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'vw_sp2i_generated_building'
ORDER BY ordinal_position;

-- Échantillon de données
SELECT 
    'vw_sp2i_generated_building' AS source,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT lot_code) AS distinct_lots,
    COUNT(DISTINCT generation_batch) AS distinct_batches,
    COUNT(DISTINCT source_table) AS distinct_source_tables,
    COUNT(DISTINCT component_code) AS distinct_components,
    ARRAY_AGG(DISTINCT source_table ORDER BY source_table) AS source_tables_list
FROM vw_sp2i_generated_building;

-- Colonnes détail
SELECT * FROM vw_sp2i_generated_building LIMIT 5;

-- ===========================================================================
-- AUDIT 3 : Structure vw_sp2i_generated_envelope
-- ===========================================================================

SELECT 
    'vw_sp2i_generated_envelope' AS view_name,
    column_name,
    ordinal_position,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'vw_sp2i_generated_envelope'
ORDER BY ordinal_position;

-- Échantillon de données
SELECT 
    'vw_sp2i_generated_envelope' AS source,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT lot_code) AS distinct_lots,
    COUNT(DISTINCT generation_batch) AS distinct_batches,
    COUNT(DISTINCT source_table) AS distinct_source_tables,
    ARRAY_AGG(DISTINCT source_table ORDER BY source_table) AS source_tables_list
FROM vw_sp2i_generated_envelope;

-- Colonnes détail
SELECT * FROM vw_sp2i_generated_envelope LIMIT 5;

-- ===========================================================================
-- AUDIT 4 : Structure vw_sp2i_generated_special_systems
-- ===========================================================================

SELECT 
    'vw_sp2i_generated_special_systems' AS view_name,
    column_name,
    ordinal_position,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'vw_sp2i_generated_special_systems'
ORDER BY ordinal_position;

-- Échantillon de données
SELECT 
    'vw_sp2i_generated_special_systems' AS source,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT lot_code) AS distinct_lots,
    COUNT(DISTINCT generation_batch) AS distinct_batches,
    COUNT(DISTINCT source_table) AS distinct_source_tables,
    ARRAY_AGG(DISTINCT source_table ORDER BY source_table) AS source_tables_list
FROM vw_sp2i_generated_special_systems;

-- Colonnes détail
SELECT * FROM vw_sp2i_generated_special_systems LIMIT 5;

-- ===========================================================================
-- AUDIT 5 : COMPARAISON DE SCHÉMA
-- ===========================================================================

-- Quelles colonnes sont communes?
WITH columns_per_view AS (
    SELECT 'vw_sp2i_generated_quantities' AS view_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'vw_sp2i_generated_quantities'
    UNION ALL
    SELECT 'vw_sp2i_generated_building', column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'vw_sp2i_generated_building'
    UNION ALL
    SELECT 'vw_sp2i_generated_envelope', column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'vw_sp2i_generated_envelope'
    UNION ALL
    SELECT 'vw_sp2i_generated_special_systems', column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'vw_sp2i_generated_special_systems'
)
SELECT 
    column_name,
    COUNT(DISTINCT view_name) AS in_how_many_views,
    ARRAY_AGG(DISTINCT view_name ORDER BY view_name) AS views_containing_column
FROM columns_per_view
GROUP BY column_name
ORDER BY in_how_many_views DESC, column_name;

-- ===========================================================================
-- AUDIT 6 : COMPTE TOTAL DE LIGNES PAR VUE
-- ===========================================================================

SELECT 
    'vw_sp2i_generated_quantities' AS source,
    COUNT(*) AS total_rows
FROM vw_sp2i_generated_quantities

UNION ALL

SELECT 
    'vw_sp2i_generated_building',
    COUNT(*)
FROM vw_sp2i_generated_building

UNION ALL

SELECT 
    'vw_sp2i_generated_envelope',
    COUNT(*)
FROM vw_sp2i_generated_envelope

UNION ALL

SELECT 
    'vw_sp2i_generated_special_systems',
    COUNT(*)
FROM vw_sp2i_generated_special_systems

UNION ALL

SELECT 
    'TOTAL_4_VUES',
    (SELECT COUNT(*) FROM vw_sp2i_generated_quantities)
    + (SELECT COUNT(*) FROM vw_sp2i_generated_building)
    + (SELECT COUNT(*) FROM vw_sp2i_generated_envelope)
    + (SELECT COUNT(*) FROM vw_sp2i_generated_special_systems);

-- ===========================================================================
-- AUDIT 7 : DISTRIBUTION PAR LOT (comparer les 4 vues)
-- ===========================================================================

WITH lots_quantities AS (
    SELECT lot_code, COUNT(*) AS qty_rows FROM vw_sp2i_generated_quantities GROUP BY lot_code
),
lots_building AS (
    SELECT lot_code, COUNT(*) AS build_rows FROM vw_sp2i_generated_building GROUP BY lot_code
),
lots_envelope AS (
    SELECT lot_code, COUNT(*) AS env_rows FROM vw_sp2i_generated_envelope GROUP BY lot_code
),
lots_special AS (
    SELECT lot_code, COUNT(*) AS special_rows FROM vw_sp2i_generated_special_systems GROUP BY lot_code
)
SELECT 
    COALESCE(q.lot_code, b.lot_code, e.lot_code, s.lot_code) AS lot_code,
    COALESCE(q.qty_rows, 0) AS quantities_rows,
    COALESCE(b.build_rows, 0) AS building_rows,
    COALESCE(e.env_rows, 0) AS envelope_rows,
    COALESCE(s.special_rows, 0) AS special_rows,
    COALESCE(q.qty_rows, 0) 
    + COALESCE(b.build_rows, 0) 
    + COALESCE(e.env_rows, 0) 
    + COALESCE(s.special_rows, 0) AS total_rows_per_lot
FROM lots_quantities q
FULL OUTER JOIN lots_building b ON q.lot_code = b.lot_code
FULL OUTER JOIN lots_envelope e ON q.lot_code = e.lot_code
FULL OUTER JOIN lots_special s ON q.lot_code = s.lot_code
ORDER BY total_rows_per_lot DESC;

-- ===========================================================================
-- AUDIT 8 : COLONNES MANQUANTES POUR LE MAPPING
-- ===========================================================================

/*
Mapping requis (selon demande métier):
- lot                    ✓ Présent dans toutes
- sous_lot              ? À auditer
- article               ? À auditer
- designation           ✓ Présent
- quantite              ✓ Présent (quantity)
- unite                 ✓ Présent (unit)
- batiment              ? À auditer (batiment_id dans quantities)
- niveau                ? À auditer (niveau_id dans quantities)
- appartement           ? À auditer (appartement dans quantities)
- piece                 ? À auditer (piece_id dans quantities)
*/

-- Vérifier quelles dimensions sont disponibles
SELECT 
    'SCHÉMA AUDIT' AS check_type,
    'lot_code' AS colonne,
    'PRÉSENT' AS status
UNION ALL SELECT '', 'generation_batch', 'PRÉSENT'
UNION ALL SELECT '', 'generated_article_code', 'PRÉSENT'
UNION ALL SELECT '', 'designation / generated_designation', 'PRÉSENT'
UNION ALL SELECT '', 'quantity', 'PRÉSENT'
UNION ALL SELECT '', 'unit', 'PRÉSENT'
UNION ALL SELECT '', 'batiment_id', 'SEULEMENT dans quantities'
UNION ALL SELECT '', 'niveau_id', 'SEULEMENT dans quantities'
UNION ALL SELECT '', 'appartement', 'SEULEMENT dans quantities'
UNION ALL SELECT '', 'piece_id', 'SEULEMENT dans quantities'
UNION ALL SELECT '', 'project_id', 'SEULEMENT dans quantities'
UNION ALL SELECT '', 'type_piece', 'SEULEMENT dans quantities'
UNION ALL SELECT '', 'source_table', 'SEULEMENT dans building/envelope/special'
UNION ALL SELECT '', 'component_index', 'SEULEMENT dans building/envelope/special'
UNION ALL SELECT '', 'scope_note', 'SEULEMENT dans building/envelope/special';

-- ===========================================================================
-- AUDIT 9 : RÉSUMÉ STRUCTUREL
-- ===========================================================================

SELECT 
    'RÉSUMÉ VUE' AS description,
    'Colonnes' AS dimension,
    'Détails' AS details

UNION ALL SELECT '', '', ''

UNION ALL SELECT 
    'vw_sp2i_generated_quantities',
    'Colonnes spécifiques',
    'project_id, batiment_id, niveau_id, appartement, piece_id, type_piece, source_quantity, source_surface_m2, quantity_formula'

UNION ALL SELECT 
    'vw_sp2i_generated_building',
    'Colonnes spécifiques',
    'source_table, component_index, scope_note'

UNION ALL SELECT 
    'vw_sp2i_generated_envelope',
    'Colonnes spécifiques',
    'source_table, component_index, scope_note'

UNION ALL SELECT 
    'vw_sp2i_generated_special_systems',
    'Colonnes spécifiques',
    'source_table, component_index, scope_note'

UNION ALL SELECT 
    'COMMUNES',
    'lot_code, generation_batch, unit, quantity, created_at',
    'Présentes dans les 4 vues'

UNION ALL SELECT 
    'ARTICLE',
    'equipment_code (qty) vs component_code (building/env/special)',
    'RÉDUCTION requise → article'

UNION ALL SELECT 
    'DESIGNATION',
    'generated_designation (qty) vs designation (others)',
    'UNIFICATION requise'

UNION ALL SELECT 
    'DIFFÉRENCE CLÉS',
    'quantities = bâtiment/niveau/appart/pièce | others = sans dimensions spatiales',
    'À résoudre avec LEFT JOIN dim_* si nécessaire';

-- ===========================================================================
-- AUDIT 10 : STRATÉGIE DE FUSION
-- ===========================================================================

/*
OPTION A : Union simple (losing spatial dims)
→ SELECT lot, generation_batch, article, designation, quantity, unit, ...
FROM vw_sp2i_generated_quantities

UNION ALL

SELECT lot, generation_batch, component_code, designation, quantity, unit, NULL, NULL, NULL, NULL, ...
FROM vw_sp2i_generated_building
... = losing batiment_id, niveau_id, appartement, piece_id

OPTION B : Union avec LEFT JOIN enrichissement (complex)
→ Building/envelope/special JOIN dim_* pour récupérer batiment/niveau/appart
→ Plus d'info mais complexe

OPTION C : Dual-path Union (recommandé)
→ Quantities = avec dimensions spatiales complètes
→ Building/envelope/special = sans dimensions spatiales (NULL acceptable)
→ Schéma unifié = colonnes optionnelles NULL si absentes
*/

-- ===========================================================================
-- FIN AUDIT - RECOMMANDATIONS
-- ===========================================================================

/*
FINDINGS:

1. COLONNES COMMUNES:
   - lot_code ✓
   - generation_batch ✓
   - quantity ✓
   - unit ✓
   - created_at ✓

2. COLONNES UNIFIABLES:
   - equipment_code (qty) + component_code (building/env/special) → article_code
   - generated_designation (qty) + designation (others) → designation

3. COLONNES SPATIALES (orphelines dans 3 vues):
   - batiment_id, niveau_id, appartement, piece_id, project_id, type_piece
   → SEULEMENT dans quantities
   → NULL pour building/envelope/special

4. COLONNES MÉTIER (orphelines dans 1 vue):
   - source_table, component_index, scope_note
   → SEULEMENT dans building/envelope/special
   → NULL ou 'N/A' pour quantities

5. ARCHITECTURE RECOMMANDÉE:
   vw_sp2i_generated_dqe_master =
   ├─ SELECT ... FROM vw_sp2i_generated_quantities (avec dims spatiales)
   └─ UNION ALL
      SELECT ... FROM building/envelope/special (sans dims spatiales = NULL)

6. LIGNES TOTALES ESTIMÉES:
   Voir AUDIT 6 pour comptes exacts

7. GO / NO GO?
   → GO SI nombre de lignes total > 1000 et cohérent
   → NO GO SI orphelins excessifs ou NULL malvenus
*/
