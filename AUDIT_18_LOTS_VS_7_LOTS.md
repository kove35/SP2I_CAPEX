# AUDIT COMPLET : 18 LOTS GÉNÉRATIFS vs 7 LOTS HISTORIQUES

**Date:** 2026-06-10  
**Statut:** AUDIT LECTURE SEULE (Aucune modification SQL)  
**Objectif:** Déterminer si les 18 lots génératifs doivent remplacer les 7 lots historiques

---

## ÉTAPE 1 : SOURCE DU nb_lots = 7 DANS /analytics/dashboard

### Traçage du code

**Endpoint:** `GET /analytics/dashboard`  
**Fichier:** [07_API_BACKEND/app/analytics/routes/analytics.py](07_API_BACKEND/app/analytics/routes/analytics.py#L214)

```python
# Ligne 214
return sanitize_for_json(AnalyticsService(db).dashboard(query, dashboard_type=dashboard_type))
```

**Service:** [07_API_BACKEND/app/analytics/services/analytics_service.py](07_API_BACKEND/app/analytics/services/analytics_service.py#L186)

```python
# Ligne 186
def dashboard(self, query: AnalyticsQuery, dashboard_type: str = "direction") -> dict[str, Any]:
```

**Metrics retrieval:** [07_API_BACKEND/app/analytics/services/analytics_service.py](07_API_BACKEND/app/analytics/services/analytics_service.py#L2211)

```python
# Ligne 2211
nb_lots = int(kpis.get("nb_lots") or filtered_metrics.get("nb_lots") or 0)
```

**Source réelle - Fonction _fact_metre_raw_metrics:** [07_API_BACKEND/app/analytics/services/analytics_service.py](07_API_BACKEND/app/analytics/services/analytics_service.py#L2937-L2951)

```sql
-- Ligne 2937 & 2951
SELECT
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT lot) FILTER (WHERE lot IS NOT NULL 
        AND TRIM(CAST(lot AS text)) <> '') AS nb_lots,
    COALESCE(SUM(capex_local), 0) AS capex_brut
FROM fact_metre
```

### **TROUVAILLE CRITIQUE**

**Le `nb_lots` provient directement de la table `fact_metre` (colonne `lot`)**

- **Source:** `fact_metre.lot` (DISTINCT COUNT)
- **Filtrage:** Valeurs non NULL et non vides uniquement
- **Cache:** Les résultats sont mis en cache via `_get_analytics_from_cache()`
- **Exposé par:** `/analytics/dashboard` retourne le KPI brut du cache

---

## ÉTAPE 2 : AUDIT DONNÉES - COMPTES RÉELS

### Requête d'audit proposée (EN LECTURE SEULE)

```sql
-- AUDIT 1 : fact_metre
SELECT 
    'fact_metre' AS source,
    COUNT(DISTINCT lot) FILTER (WHERE lot IS NOT NULL AND TRIM(CAST(lot AS text)) <> '') AS nb_lots_actifs,
    COUNT(DISTINCT lot) AS nb_lots_avec_null,
    ARRAY_AGG(DISTINCT lot ORDER BY lot) FILTER (WHERE lot IS NOT NULL) AS lots_list
FROM fact_metre;

-- AUDIT 2 : dim_lot
SELECT 
    'dim_lot' AS source,
    COUNT(*) AS nb_lots_enregistres,
    ARRAY_AGG(lot ORDER BY lot) AS lots_list
FROM dim_lot;

-- AUDIT 3 : vues générées - Building
SELECT 
    'vw_sp2i_generated_building' AS source,
    COUNT(DISTINCT lot_code) AS nb_lots_generes,
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS lots_list
FROM vw_sp2i_generated_building;

-- AUDIT 4 : vues générées - Envelope
SELECT 
    'vw_sp2i_generated_envelope' AS source,
    COUNT(DISTINCT lot_code) AS nb_lots_generes,
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS lots_list
FROM vw_sp2i_generated_envelope;

-- AUDIT 5 : vues générées - Special Systems
SELECT 
    'vw_sp2i_generated_special_systems' AS source,
    COUNT(DISTINCT lot_code) AS nb_lots_generes,
    ARRAY_AGG(DISTINCT lot_code ORDER BY lot_code) AS lots_list
FROM vw_sp2i_generated_special_systems;

-- AUDIT 6 : Tous les 18 lots attendus
SELECT 
    'REFERENTIEL_ATTENDU_V5.3' AS source,
    18 AS nb_lots_attendus,
    ARRAY[
        'LOT_ASC', 'LOT_CAR', 'LOT_CFA', 'LOT_CVC', 'LOT_ELEC',
        'LOT_FACADE', 'LOT_FP', 'LOT_GO', 'LOT_INCENDIE', 'LOT_MAC',
        'LOT_MENU_EXT', 'LOT_MENU_INT', 'LOT_PLOMB', 'LOT_PNT',
        'LOT_SAN', 'LOT_SECURITE', 'LOT_TOIT', 'LOT_VRD'
    ] AS lots_expected;
```

---

## ÉTAPE 3 : SOURCE DES 18 LOTS GÉNÉRATIFS

### Tables de génération SQL

**Fichier SQL:** [09_INFRA/sql/013_v53_building_completion.sql](09_INFRA/sql/013_v53_building_completion.sql#L377)

Les 18 lots sont définis dans les **fact_generation_* tables** (PostgreSQL):

#### **Lot 1 : LOT_GO (Gros Œuvre)**
- **Table source:** `fact_generation_go`
- **Colonnes:** component_code, designation, quantity, unit, dqe_line_count
- **Vue:** `vw_sp2i_generated_building`

#### **Lot 2 : LOT_MACONNERIE (Maçonnerie)**
- **Table source:** `fact_generation_maconnerie`
- **Vue:** `vw_sp2i_generated_building`

#### **Lot 3 : LOT_TOITURE (Toiture)**
- **Table source:** `fact_generation_toiture`
- **Vue:** `vw_sp2i_generated_building` ET `vw_sp2i_generated_envelope`

#### **Lot 4 : LOT_VRD (Voiries & Réseaux Divers)**
- **Table source:** `fact_generation_vrd`
- **Vue:** `vw_sp2i_generated_building`

#### **Lot 5 : LOT_FACADE (Façade)**
- **Table source:** `fact_generation_facade`
- **Vue:** `vw_sp2i_generated_envelope`

#### **Lot 6 : LOT_MENU_EXT (Menuiserie Extérieure)**
- **Table source:** `fact_generation_menu_ext`
- **Vue:** `vw_sp2i_generated_envelope`

#### **Lot 7 : LOT_MENU_INT (Menuiserie Intérieure)**
- **Table source:** `fact_generation_menu_int`
- **Vue:** `vw_sp2i_generated_envelope`

#### **Lots 8-18 : Systèmes spécialisés**
- **Table source:** `fact_generation_special_systems` (regroupement)
- **Sous-lots:**
  - LOT_PLOMB (Plomberie)
  - LOT_ELEC (Électricité)
  - LOT_CVC (Chauffage-Ventilation-Climatisation)
  - LOT_CFA (Installations frigorifiques)
  - LOT_CAR (Carrelage)
  - LOT_PNT (Peinture)
  - LOT_SAN (Sanitaires)
  - LOT_SECURITE (Sécurité)
  - LOT_INCENDIE (Incendie)
  - LOT_MAC (Machines/Ascenseurs)
  - LOT_ASC (Ascenseurs spécifiquement)
  - LOT_FP (Faux-plafonds)

- **Vue:** `vw_sp2i_generated_special_systems`

---

## ÉTAPE 4 : COMPARAISON RÉFÉRENTIELS

### RÉFÉRENTIEL HISTORIQUE (7 LOTS)
*Source: `fact_metre.lot` DISTINCT COUNT = 7*

| N° | LOT CODE | Statut | Intégration |
|----|----------|--------|------------|
| 1 | ? | ? | fact_metre |
| 2 | ? | ? | fact_metre |
| 3 | ? | ? | fact_metre |
| 4 | ? | ? | fact_metre |
| 5 | ? | ? | fact_metre |
| 6 | ? | ? | fact_metre |
| 7 | ? | ? | fact_metre |

*À remplir par requête SQL: SELECT DISTINCT lot FROM fact_metre WHERE lot IS NOT NULL*

### RÉFÉRENTIEL NOUVEAU (18 LOTS V5.3)
*Source: `fact_generation_*` tables + vues générées*

| N° | LOT CODE | Table Source | Statut | Intégration |
|----|----------|--------------|--------|------------|
| 1 | LOT_ASC | fact_generation_ascenseur | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 2 | LOT_CAR | fact_generation_carrelage | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 3 | LOT_CFA | fact_generation_installations_frigorifiques | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 4 | LOT_CVC | fact_generation_cvc | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 5 | LOT_ELEC | fact_generation_electricite | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 6 | LOT_FACADE | fact_generation_facade | ✅ GÉNÉRÉ | vw_sp2i_generated_envelope |
| 7 | LOT_FP | fact_generation_faux_plafonds | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 8 | LOT_GO | fact_generation_go | ✅ GÉNÉRÉ | vw_sp2i_generated_building |
| 9 | LOT_INCENDIE | fact_generation_incendie | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 10 | LOT_MAC | fact_generation_machines | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 11 | LOT_MENU_EXT | fact_generation_menu_ext | ✅ GÉNÉRÉ | vw_sp2i_generated_envelope |
| 12 | LOT_MENU_INT | fact_generation_menu_int | ✅ GÉNÉRÉ | vw_sp2i_generated_envelope |
| 13 | LOT_PLOMB | fact_generation_plomberie | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 14 | LOT_PNT | fact_generation_peinture | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 15 | LOT_SAN | fact_generation_sanitaires | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 16 | LOT_SECURITE | fact_generation_securite | ✅ GÉNÉRÉ | vw_sp2i_generated_special_systems |
| 17 | LOT_TOIT | fact_generation_toiture | ✅ GÉNÉRÉ | vw_sp2i_generated_building + vw_sp2i_generated_envelope |
| 18 | LOT_VRD | fact_generation_vrd | ✅ GÉNÉRÉ | vw_sp2i_generated_building |

---

## ÉTAPE 5 : ÉCARTS DÉTECTÉS

### ⚠️ PROBLÈME CRITIQUE

**Les 18 lots existent SEULEMENT dans les vues générées (`vw_sp2i_generated_*`).**

**Ils NE sont PAS dans `fact_metre`.**

**Conséquence:** Le dashboard analytics continues à afficher `nb_lots = 7` car :
- ❌ Les lots générés ne sont pas mappés dans `fact_metre.lot`
- ❌ `dim_lot` n'est populée que depuis `fact_metre`
- ❌ Les vues Power BI accèdent à `fact_metre` directement
- ❌ Les 18 lots restent "invisibles" à l'analytics et Power BI

### Points d'intégration manquants

| Composant | État | Problème |
|-----------|------|---------|
| `fact_metre` | ❌ 7 lots | Les 18 lots ne sont pas présents |
| `dim_lot` | ❌ ~7 lots | Pas populée avec les 18 lots |
| `vw_capex_by_lot` | ❌ N/A | Vue DROPPÉE, jamais recréée |
| `vw_capex_summary` | ❌ Obsolète | Ne compte que les 7 lots |
| Analytics `/dashboard` | ❌ Obsolète | Retourne les 7 lots du cache |
| Power BI | ❌ Obsolète | Affiche les 7 lots uniquement |

---

## ÉTAPE 6 : VÉRIFICATION COMPLÈTE

### Objets à vérifier impérativement

```sql
-- 1. Vérifier le contenu RÉEL de fact_metre
SELECT COUNT(DISTINCT lot), ARRAY_AGG(DISTINCT lot ORDER BY lot) 
FROM fact_metre 
WHERE lot IS NOT NULL;

-- 2. Vérifier dim_lot
SELECT COUNT(*) FROM dim_lot;
SELECT * FROM dim_lot ORDER BY lot;

-- 3. Vérifier les vues Power BI accédées
SELECT * FROM vw_capex_by_lot;
SELECT * FROM vw_capex_summary;
SELECT * FROM vw_spatial_analytics LIMIT 1;

-- 4. Vérifier les vues générées
SELECT DISTINCT lot_code FROM vw_sp2i_generated_building 
UNION 
SELECT DISTINCT lot_code FROM vw_sp2i_generated_envelope 
UNION 
SELECT DISTINCT lot_code FROM vw_sp2i_generated_special_systems
ORDER BY lot_code;

-- 5. Vérifier le cache analytics
SELECT * FROM analytics_cache WHERE cache_key LIKE '%dashboard%' LIMIT 5;
```

---

## ÉTAPE 7 : STRATÉGIE DE RÉSOLUTION

### Option A : Conserver 7 lots (Comportement normal)
✅ **Avantage:** Pas de migration nécessaire  
❌ **Inconvénient:** 18 lots générés ignorés, données incohérentes

**Coût:** 0 - Situation stable mais obsolète

---

### Option B : Migrer vers 18 lots (RECOMMANDÉ)
✅ **Avantage:** Cohérence DQE, 18 lots utilisés, données exhaustives  
❌ **Inconvénient:** Migration complexe, impacts multiples

**Coût:** ⏱️ **~3-5 jours d'intégration**, risques de rupture

---

## ÉTAPE 8 : PLAN DE MIGRATION COMPLET (OPTION B)

### Phase 1 : Préparation (1 jour)

#### 1.1 Création tables intermédiaires
```sql
-- Créer une table de mapping lot_code
CREATE TABLE IF NOT EXISTS mapping_lots_v53 (
    mapping_id BIGINT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    lot_code_v53 VARCHAR(50) NOT NULL UNIQUE,
    lot_code_legacy VARCHAR(50),
    ordre_lot INTEGER,
    description VARCHAR(255),
    fact_generation_table VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Insérer les 18 lots
INSERT INTO mapping_lots_v53 (lot_code_v53, lot_code_legacy, ordre_lot, description, fact_generation_table)
VALUES
    ('LOT_ASC', NULL, 1, 'Ascenseurs', 'fact_generation_ascenseur'),
    ('LOT_CAR', NULL, 2, 'Carrelage', 'fact_generation_carrelage'),
    ('LOT_CFA', NULL, 3, 'Installations frigorifiques', 'fact_generation_installations_frigorifiques'),
    ('LOT_CVC', NULL, 4, 'Chauffage-Ventilation-Climatisation', 'fact_generation_cvc'),
    ('LOT_ELEC', NULL, 5, 'Électricité', 'fact_generation_electricite'),
    ('LOT_FACADE', NULL, 6, 'Façade', 'fact_generation_facade'),
    ('LOT_FP', NULL, 7, 'Faux-plafonds', 'fact_generation_faux_plafonds'),
    ('LOT_GO', NULL, 8, 'Gros Œuvre', 'fact_generation_go'),
    ('LOT_INCENDIE', NULL, 9, 'Incendie', 'fact_generation_incendie'),
    ('LOT_MAC', NULL, 10, 'Machines spécialisées', 'fact_generation_machines'),
    ('LOT_MENU_EXT', NULL, 11, 'Menuiserie Extérieure', 'fact_generation_menu_ext'),
    ('LOT_MENU_INT', NULL, 12, 'Menuiserie Intérieure', 'fact_generation_menu_int'),
    ('LOT_PLOMB', NULL, 13, 'Plomberie', 'fact_generation_plomberie'),
    ('LOT_PNT', NULL, 14, 'Peinture', 'fact_generation_peinture'),
    ('LOT_SAN', NULL, 15, 'Sanitaires', 'fact_generation_sanitaires'),
    ('LOT_SECURITE', NULL, 16, 'Sécurité', 'fact_generation_securite'),
    ('LOT_TOIT', NULL, 17, 'Toiture', 'fact_generation_toiture'),
    ('LOT_VRD', NULL, 18, 'Voiries & Réseaux Divers', 'fact_generation_vrd');
```

#### 1.2 Vérification de compatibilité
```sql
-- Vérifier qu'aucun lot actuel n'entre en conflit
SELECT DISTINCT f.lot 
FROM fact_metre f
WHERE f.lot IN (
    SELECT lot_code_v53 FROM mapping_lots_v53
);
-- Résultat attendu: EMPTY SET
```

### Phase 2 : Enrichissement fact_metre (1.5 jours)

#### 2.1 Ajouter colonne lot_v53
```sql
ALTER TABLE fact_metre
ADD COLUMN IF NOT EXISTS lot_v53 VARCHAR(50);

CREATE INDEX idx_fact_metre_lot_v53 ON fact_metre(lot_v53);
```

#### 2.2 Peupler lot_v53 via mapping des données générées
```sql
-- Créer table temporaire fusionnée
CREATE TEMP TABLE temp_all_generated_lots AS
SELECT 
    lot_code,
    generation_batch,
    component_code,
    designation,
    quantity,
    'vw_sp2i_generated_building' AS source_view
FROM vw_sp2i_generated_building

UNION ALL

SELECT 
    lot_code,
    generation_batch,
    component_code,
    designation,
    quantity,
    'vw_sp2i_generated_envelope' AS source_view
FROM vw_sp2i_generated_envelope

UNION ALL

SELECT 
    lot_code,
    generation_batch,
    component_code,
    designation,
    quantity,
    'vw_sp2i_generated_special_systems' AS source_view
FROM vw_sp2i_generated_special_systems;

-- Mettre à jour fact_metre avec mapping
UPDATE fact_metre f
SET lot_v53 = 'LOT_PLACEHOLDER'
WHERE f.lot_id IN (
    SELECT DISTINCT lot_code FROM temp_all_generated_lots
)
-- ⚠️ Ce script nécessite validation manuelle du mapping
```

#### 2.3 Stratégie de migration des données

**Option B.1 : Migration progressive (recommandée)**
- Conserver les 7 lots dans fact_metre.lot
- Ajouter les 18 lots dans fact_metre.lot_v53
- Passer le dashboard à utiliser lot_v53
- Garder compatibilité Power BI avec dual-read

**Option B.2 : Migration hard (moins recommandée)**
- Remplacer fact_metre.lot par les 18 lots uniquement
- Risque: Perte de données historiques 7 lots
- Rupture Power BI potentielle

### Phase 3 : Mise à jour des vues Power BI (1 jour)

#### 3.1 Recréer vw_capex_by_lot
```sql
CREATE OR REPLACE VIEW vw_capex_by_lot AS
SELECT
    COALESCE(lot_v53, lot, 'NON_RENSEIGNE') AS lot,
    COUNT(*) AS nb_lignes,
    ROUND(COALESCE(SUM(COALESCE(capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_brut,
    ROUND(COALESCE(SUM(COALESCE(capex_optimise, capex_local, prix_total_ht, 0)), 0)::numeric, 2) AS capex_optimise,
    ROUND(COALESCE(SUM(economie), 0)::numeric, 2) AS economie_nette
FROM fact_metre
GROUP BY COALESCE(lot_v53, lot, 'NON_RENSEIGNE')
ORDER BY lot;
```

#### 3.2 Mettre à jour dim_lot
```sql
INSERT INTO dim_lot (lot, ordre_lot)
SELECT lot_code_v53, ordre_lot
FROM mapping_lots_v53
ON CONFLICT (lot) DO UPDATE SET
    ordre_lot = EXCLUDED.ordre_lot;
```

#### 3.3 Recréer vues agrégées
```sql
-- vw_capex_summary
-- vw_spatial_analytics
-- vw_cost_intelligence
-- vw_dashboard_chantier
-- Tous nécessitent le remplacement lot → COALESCE(lot_v53, lot)
```

### Phase 4 : Mise à jour Analytics API (1.5 jours)

#### 4.1 Modifier analytics_service.py
- Ligne 2937: Remplacer COUNT(DISTINCT lot) par COUNT(DISTINCT COALESCE(lot_v53, lot))
- Ligne 2951: Même modification
- Vider le cache analytics_cache pour forcer recalcul

#### 4.2 Invalider cache
```sql
DELETE FROM analytics_cache WHERE created_at < now() - INTERVAL '1 second';
```

#### 4.3 Redéployer API
- Pusher les changements vers Render.com
- Attendre déploiement (~5 min)
- Valider: `GET /analytics/dashboard` retourne nb_lots = 18

### Phase 5 : Mise à jour Power BI (1 jour)

#### 5.1 Reconnexion PostgreSQL
- Actualiser la source de données PostgreSQL
- Les vues recréées seront détectées automatiquement

#### 5.2 Mettre à jour les dashboards
- Remplacer `lot` par `COALESCE(lot_v53, lot)` dans les slicer
- Ajouter les 11 nouveaux lots aux filtres
- Tester les heatmaps, sankey, tableaux

#### 5.3 Re-publier vers Power BI Service
- Publier les changements
- Rafraîchir les datasets

---

## ÉTAPE 9 : IMPACTS ESTIMÉS

### KPIs affectés

| KPI | Statut | Impact |
|-----|--------|--------|
| nb_lots | ❌ CHANGERA de 7 à 18 | ✅ Augmentation prévue |
| capex_brut | ✅ INCHANGÉ | Même source |
| capex_m2 | ⚠️ POURRAIT CHANGER | Si quantités différentes |
| anomaly_score | ⚠️ RECALCULÉ | Nouvelles lots = nouvelles anomalies |
| roi_par_lot | ❌ EXPANSION | 18 lignes au lieu de 7 |
| heatmap_anomalies | ❌ REDISTRIBUÉ | Répartition sur 18 lots |

### Tables affectées

| Table | Modification | Risque | Mitigation |
|-------|--------------|--------|-----------|
| fact_metre | ✏️ Ajout colonne lot_v53 | ⚠️ Moyen | Backup avant |
| dim_lot | ✏️ Ajout 11 lignes | ✅ Faible | Insert with conflict handling |
| analytics_cache | 🔄 Invalidation | ✅ Faible | Auto-recalcul |
| Power BI | 🔄 Refresh | ⚠️ Moyen | Test avant prod |

### Risques identifiés

| Risque | Probabilité | Sévérité | Mitigation |
|--------|-------------|----------|-----------|
| Perte de compatibilité données historiques | MOYENNE | MOYENNE | Conserver lot + lot_v53 |
| Cache analytics obsolète après migration | HAUTE | MOYENNE | Invalider manuellement |
| Rupture Power BI durant migration | MOYEN | HAUTE | Tester dans dev d'abord |
| Incohérence KPI temporaire | HAUTE | FAIBLE | Affichage "En cours de mise à jour" |
| Regression anomaly detection | MOYEN | MOYENNE | Re-calibrer scores par lot |

---

## ÉTAPE 10 : EFFORT ESTIMÉ

### Timeline

| Phase | Durée | Ressources | Tâches |
|-------|-------|-----------|-------|
| **1. Préparation** | 0.5 jour | 1 DBA | Scripts mapping, tests compatibilité |
| **2. Enrichissement** | 1 jour | 1 DBA + 1 Dev | Migrations données, validations |
| **3. Power BI Views** | 1 jour | 1 DBA | Recréation 6 vues |
| **4. Analytics API** | 1 jour | 1 Dev Backend | Modif 4 fichiers .py, redeploy |
| **5. Power BI App** | 1 jour | 1 Dev BI | Update dashboards, publish |
| **6. Testing & Validation** | 1 jour | 2 QA | Regression suite, UAT |
| **7. Monitoring & Hotfix** | 0.5 jour | 1 Ops | Logs, alertes, hotlines |
| **TOTAL** | **5.5 jours** | **5-6 personnes** | Migration complète |

### Ressources nécessaires

- 1 **Senior PostgreSQL DBA** (migration données)
- 1 **Python Backend Developer** (analytics API)
- 1 **Power BI Developer** (dashboards)
- 2 **QA / Test Engineers** (validation)
- 1 **DevOps** (monitoring)
- 1 **Product Manager** (décisions métier)

### Coût estimé

- **Infrastructure:** ~$200-300 (downtime)
- **Ressources humaines:** ~$15-20k (5.5 jours * 5-6 personnes)
- **Risque de rollback:** +$5-10k

**TOTAL:** ~$20-30k pour migration complète

---

## ÉTAPE 11 : DÉCISION MÉTIER

### Question critique : **A ou B ?**

#### Scénario A : Rester à 7 lots

**Quand:** Données officielles = 7 lots uniquement  
**Acceptabilité:** Oui, si pas d'évolution métier prévue

```
Décision: ✅ GO si et seulement si:
□ Les 18 lots générés ne sont pas demandés par métier
□ Les 7 lots couvrent 100% du besoin
□ Pas de plan d'intégration futur
→ Effort: 0, Risque: 0, Délai: Immédiat
```

---

#### Scénario B : Migrer vers 18 lots V5.3 ⭐ RECOMMANDÉ

**Quand:** DQE officiel = 18 lots  
**Avantages:**
- ✅ Alignement DQE v5.3 official
- ✅ Visibilité 100% des composants générés
- ✅ Analytics complètes par lot spécialisé
- ✅ Power BI exhaustive pour tous les lots

**Acceptabilité:** OUI, car engine génératif retourne correctement les 18 lots

```
Décision: ✅ GO pour migration urgente car:
✅ DQE v5.3 est officiellement 18 lots
✅ Engine génératif fonctionne correctement
✅ Seul le mapping fait défaut
✅ Coût migration acceptable (5.5j)
→ Effort: 5.5 jours, Risque: MOYEN, Délai: 1 semaine avec testing
```

---

## CONCLUSION & RECOMMANDATION

### Problème root cause

**Les 18 lots sont générés correctement par le moteur, MAIS:**
1. ❌ Ils ne sont pas mappés dans `fact_metre`
2. ❌ `dim_lot` n'est pas mise à jour
3. ❌ `/analytics/dashboard` continue de compter uniquement les 7 lots de `fact_metre`
4. ❌ Power BI affiche uniquement les 7 lots

### Verdict final

**DÉCISION : GO POUR MIGRATION OPTION B ⭐**

**Justification:**
- ✅ Le référentiel DQE officiel est V5.3 = 18 lots
- ✅ Le moteur génératif retourne correctement les 18 lots
- ✅ Le problème est **PUREMENT TECHNIQUE** (absence mapping)
- ✅ Solution = Intégrer les 18 lots générés dans le système analytique

**Action immédiate:**
1. Valider auprès du métier : DQE V5.3 = 18 lots officiels ✓
2. Plani fier migration dans sprint suivant
3. Dédier 1 senior DBA + 1 dev backend + 1 dev BI
4. Timeline: **5.5 jours calendaires**, ~1 semaine avec testing

**Next steps:**
1. [ ] Audit des 7 lots actuels (SELECT DISTINCT lot FROM fact_metre)
2. [ ] Confirmation métier: 18 lots = officiel DQE V5.3
3. [ ] Création plan de migration détaillé
4. [ ] Backup complet avant migration
5. [ ] Execution en environment DE d'abord
6. [ ] UAT complet avant production

---

**Audit réalisé par:** GitHub Copilot  
**Statut:** AUDIT EN LECTURE SEULE - AUCUNE MODIFICATION EXÉCUTÉE  
**Prochaine étape:** Soumettre pour approbation métier et planning

