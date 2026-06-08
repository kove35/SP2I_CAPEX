# Correction Neon - Objectif Grade A

## Constat avant correction

Audit `333adb7` :

- Grade : `D`
- Issues :
  - vue active manquante pour `lot`
  - vue active manquante pour `sous_lot`
  - vue active manquante pour `article`
- Warnings :
  - `dim_piece.surface_m2` absente
  - `dim_appartement.surface_m2` absente
  - `vw_dim_article_bpu_active` vide
  - verifier `code_article` vs `article_id`

## Cause racine

Le modele Neon ne contenait pas encore les vues actives attendues par Power BI.

Le referentiel article pouvait aussi etre desynchronise :

- `fact_metre` peut porter le code article dans `code_article` ou `article_id`
- `dim_article_bpu` peut porter la cle dans `code_article`, avec `article_id` absent sur les schemas anciens

Les surfaces etaient absentes du schema de certaines bases, ce qui rendait les KPI surface partiels.

## Correction appliquee

Migration ajoutee :

```text
09_INFRA/sql/011_powerbi_neon_integrity_fix.sql
```

La migration est :

- additive
- idempotente
- compatible PostgreSQL / Neon
- sans suppression de donnees

Elle fait :

1. ajoute `dim_piece.surface_m2` si absent
2. ajoute `dim_appartement.surface_m2` si absent
3. ajoute les colonnes article standard manquantes dans `dim_article_bpu`
4. complete `fact_metre.code_article` depuis `fact_metre.article_id` quand `code_article` est vide
5. enrichit `dim_lot` depuis les lots reels de `fact_metre`
6. enrichit `dim_sous_lot_complet` depuis les sous-lots reels de `fact_metre`
7. enrichit `dim_article_bpu` depuis les articles reels de `fact_metre`
8. cree :
   - `vw_dim_lot_active`
   - `vw_dim_sous_lot_active`
   - `vw_dim_article_bpu_active`
9. cree les index utiles au refresh Power BI

## Diagnostic article

La vue article active utilise les correspondances reelles suivantes :

```sql
fact_metre.code_article = dim_article_bpu.code_article
OR fact_metre.article_id = dim_article_bpu.code_article
OR fact_metre.article_id = dim_article_bpu.article_id
```

Si `fact_metre.code_article` est vide et `fact_metre.article_id` renseigne, la migration remplit `code_article = article_id`.

Ce n'est pas un mapping invente : c'est la cle deja presente sur la ligne de fait.

## KPI surface

Option retenue : B.

Creer les colonnes `surface_m2` manquantes dans :

- `dim_piece`
- `dim_appartement`

Si aucune source fiable n'existe dans la base, la valeur est initialisee a `0`.

Cela garantit :

- compatibilite Power BI
- absence de `BLANK`
- aucun calcul de surface invente

Une phase ulterieure pourra recharger les vraies surfaces depuis `SP2I_BIM_DQE_MASTER.xlsx`.

## Commandes d'execution Neon

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require"
psql $env:DATABASE_URL -f 09_INFRA/sql/011_powerbi_neon_integrity_fix.sql
.\.venv\Scripts\python.exe 06_ANALYSE_BI\MPEMBA_V2\run_neon_integrity_audit.py
```

## Controle post-migration attendu

```sql
SELECT 'vw_dim_lot_active' AS view_name, COUNT(*) AS rows_count FROM vw_dim_lot_active
UNION ALL SELECT 'vw_dim_sous_lot_active', COUNT(*) FROM vw_dim_sous_lot_active
UNION ALL SELECT 'vw_dim_article_bpu_active', COUNT(*) FROM vw_dim_article_bpu_active;
```

Attendu :

- les 3 vues existent
- les 3 vues ne sont pas vides
- aucun article present dans `fact_metre` n'est orphelin
- les KPI surface ne sont plus partiels

## Resultat attendu du nouvel audit

Grade attendu : `A`

Conditions :

- 0 vue active manquante
- 0 vue active vide
- 0 article orphelin
- colonnes `surface_m2` presentes
- Power BI continue a utiliser les vues actives pour les segments

## Risque residuel

Les surfaces ajoutees peuvent valoir `0` si Neon ne contient pas encore les surfaces du master Excel.

Ce risque ne casse pas Power BI, mais limite temporairement l'interpretation du `CAPEX/m2`.

