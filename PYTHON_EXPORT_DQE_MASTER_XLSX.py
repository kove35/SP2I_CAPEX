-- ============================================================================
-- SCRIPT D'EXPORT : DQE_MPEMBA_V53_18_LOTS_MASTER.xlsx
-- Génère l'export Excel après validation de la vue maître
-- ============================================================================
-- À exécuter APRÈS création réussie de vw_sp2i_generated_dqe_master
-- Mode PYTHON + psycopg2
-- ============================================================================

import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime
import os

# ===========================================================================
# CONFIGURATION
# ===========================================================================

# Connexion PostgreSQL
DB_CONFIG = {
    'host': 'localhost',  # À adapter
    'port': 5432,
    'database': 'sp2i_capex',
    'user': 'postgres',
    'password': '***'
}

# Fichiers de sortie
OUTPUT_DIR = '/path/to/04_RESULTATS/'  # À adapter
EXPORT_DATE = datetime.now().strftime('%Y%m%d_%H%M%S')
EXCEL_FILE = f'{OUTPUT_DIR}DQE_MPEMBA_V53_18_LOTS_MASTER_{EXPORT_DATE}.xlsx'

# ===========================================================================
# 1. CONNEXION & EXTRACTION DONNÉES
# ===========================================================================

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print(f"✓ Connexion PostgreSQL établie")
    
    # Query principale - DQE complète
    query_master = """
    SELECT 
        dqe_master_id,
        generation_source,
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
        type_piece,
        source_table,
        component_index,
        scope_note,
        source_quantity,
        source_surface_m2,
        quantity_formula,
        generation_batch,
        created_at,
        inserted_at
    FROM vw_sp2i_generated_dqe_master
    ORDER BY lot_code, article_code, dqe_master_id
    """
    
    print("✓ Extraction DQE complète...")
    df_master = pd.read_sql(query_master, conn)
    print(f"  → {len(df_master)} lignes extraites")
    
    # Query résumé par lot
    query_summary_lot = """
    SELECT 
        lot_code,
        COUNT(*) AS nb_lignes,
        COUNT(DISTINCT article_code) AS nb_articles,
        COUNT(DISTINCT generation_source) AS nb_sources,
        ROUND(SUM(quantity)::numeric, 2) AS quantite_totale,
        STRING_AGG(DISTINCT unit, ', ' ORDER BY unit) AS units_used,
        ARRAY_AGG(DISTINCT generation_source ORDER BY generation_source) AS sources
    FROM vw_sp2i_generated_dqe_master
    GROUP BY lot_code
    ORDER BY lot_code
    """
    
    print("✓ Extraction résumé par lot...")
    df_summary_lot = pd.read_sql(query_summary_lot, conn)
    print(f"  → {len(df_summary_lot)} lots résumés")
    
    # Query résumé par source
    query_summary_source = """
    SELECT 
        generation_source,
        COUNT(*) AS nb_lignes,
        COUNT(DISTINCT lot_code) AS nb_lots,
        COUNT(DISTINCT article_code) AS nb_articles_uniques,
        COUNT(DISTINCT generation_batch) AS nb_batches,
        ROUND(SUM(quantity)::numeric, 2) AS quantite_totale,
        MIN(created_at) AS first_created,
        MAX(created_at) AS last_created
    FROM vw_sp2i_generated_dqe_master
    GROUP BY generation_source
    ORDER BY generation_source
    """
    
    print("✓ Extraction résumé par source...")
    df_summary_source = pd.read_sql(query_summary_source, conn)
    print(f"  → {len(df_summary_source)} sources résumées")
    
    # Query validation
    query_validation = """
    SELECT 
        'VALIDATION' AS check_type,
        COUNT(*) AS total_lignes,
        COUNT(DISTINCT lot_code) AS distinct_lots,
        COUNT(DISTINCT article_code) AS distinct_articles,
        COUNT(DISTINCT generation_batch) AS distinct_batches,
        COUNT(*) FILTER (WHERE batiment_id IS NOT NULL) AS rows_with_spatial,
        COUNT(*) FILTER (WHERE source_table IS NOT NULL) AS rows_with_source_table,
        COUNT(*) FILTER (WHERE project_id IS NULL) AS expected_nulls_project_id
    FROM vw_sp2i_generated_dqe_master
    """
    
    print("✓ Extraction validation...")
    df_validation = pd.read_sql(query_validation, conn)
    
    conn.close()
    print("✓ Connexion PostgreSQL fermée")
    
except Exception as e:
    print(f"❌ Erreur connexion/extraction: {e}")
    exit(1)

# ===========================================================================
# 2. NETTOYAGE & ENRICHISSEMENT DONNÉES
# ===========================================================================

print("\n✓ Nettoyage données...")

# Remplacer None par 'N/A' pour colonnes nullable
nullable_cols = ['batiment_id', 'niveau_id', 'appartement', 'piece_id', 
                 'type_piece', 'source_table', 'scope_note']

for col in nullable_cols:
    if col in df_master.columns:
        df_master[col] = df_master[col].fillna('N/A')

# Format dates
df_master['created_at'] = pd.to_datetime(df_master['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
df_master['inserted_at'] = pd.to_datetime(df_master['inserted_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

# Arrondir quantités
df_master['quantity'] = df_master['quantity'].round(4)

print(f"  → {len(df_master)} lignes nettoyées")

# ===========================================================================
# 3. CRÉATION FICHIER EXCEL
# ===========================================================================

print(f"\n✓ Création Excel: {EXCEL_FILE}...")

try:
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        # Sheet 1: DQE Complète
        df_master.to_excel(writer, sheet_name='DQE_COMPLETE', index=False)
        ws_master = writer.sheets['DQE_COMPLETE']
        ws_master.column_dimensions['A'].width = 12
        ws_master.column_dimensions['D'].width = 20
        ws_master.column_dimensions['E'].width = 25
        ws_master.column_dimensions['F'].width = 40
        
        # Sheet 2: Résumé par LOT
        df_summary_lot.to_excel(writer, sheet_name='SUMMARY_LOT', index=False)
        ws_lot = writer.sheets['SUMMARY_LOT']
        ws_lot.column_dimensions['A'].width = 15
        ws_lot.column_dimensions['F'].width = 15
        
        # Sheet 3: Résumé par SOURCE
        df_summary_source.to_excel(writer, sheet_name='SUMMARY_SOURCE', index=False)
        ws_src = writer.sheets['SUMMARY_SOURCE']
        ws_src.column_dimensions['A'].width = 15
        
        # Sheet 4: Validation métadonnées
        df_validation.to_excel(writer, sheet_name='VALIDATION', index=False)
        
        print("✓ Excel créé avec succès")
        print(f"  → Sheet 'DQE_COMPLETE': {len(df_master)} lignes")
        print(f"  → Sheet 'SUMMARY_LOT': {len(df_summary_lot)} lots")
        print(f"  → Sheet 'SUMMARY_SOURCE': {len(df_summary_source)} sources")
        
except Exception as e:
    print(f"❌ Erreur création Excel: {e}")
    exit(1)

# ===========================================================================
# 4. RAPPORT RÉCAPITULATIF
# ===========================================================================

print("\n" + "="*70)
print("RAPPORT D'EXPORT - DQE MPEMBA V5.3 (18 LOTS)")
print("="*70)

print(f"\nFichier: {EXCEL_FILE}")
print(f"Généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print("\n📊 STATISTIQUES:")
print(f"  • Total lignes DQE: {len(df_master):,}")
print(f"  • Lots présents: {df_master['lot_code'].nunique()}")
print(f"  • Articles uniques: {df_master['article_code'].nunique():,}")
print(f"  • Batches génération: {df_master['generation_batch'].nunique()}")

print("\n📍 RÉPARTITION PAR SOURCE:")
for _, row in df_summary_source.iterrows():
    print(f"  • {row['generation_source']:12} : {row['nb_lignes']:6,} lignes ({row['nb_lots']:2} lots, {row['nb_articles_uniques']:4,} articles)")

print("\n📋 TONS PAR LOT (top 5):")
top_lots = df_summary_lot.nlargest(5, 'nb_lignes')[['lot_code', 'nb_lignes', 'quantite_totale']]
for _, row in top_lots.iterrows():
    print(f"  • {row['lot_code']:15} : {row['nb_lignes']:6,} lignes (qty: {row['quantite_totale']:>10})")

print("\n✅ VALIDATION:")
print(f"  • Lignes avec dimensions spatiales: {df_validation['rows_with_spatial'].values[0]:,}")
print(f"  • Lignes avec source_table: {df_validation['rows_with_source_table'].values[0]:,}")
print(f"  • Orphelins (expected NULLs): {df_validation['expected_nulls_project_id'].values[0]:,}")

print("\n✓ Export terminé avec succès!")
print("="*70)

# ===========================================================================
# 5. EXPORT COMPLÉMENTAIRES (optionnel)
# ===========================================================================

# CSV
csv_file = EXCEL_FILE.replace('.xlsx', '.csv')
print(f"\n✓ Export CSV: {csv_file}")
df_master.to_csv(csv_file, index=False, encoding='utf-8-sig')

print("\n✅ Tous les exports sont prêts")
print(f"   Excel: {EXCEL_FILE}")
print(f"   CSV:   {csv_file}")

# ===========================================================================
# FIN SCRIPT
# ============================================================================
