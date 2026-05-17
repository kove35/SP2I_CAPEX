# Rapport QA Analytics SP2I CAPEX

Date : 2026-05-17

Phase : production analytics validation

## Synthese

Le dataset officiel `SP2I_CAPEX_DEMO_V1.xlsx` a ete cree, versionne et valide localement.

Le moteur IA/ETL local lit correctement le fichier :

- 584 lignes METRE normalisees
- 14 lots detectes
- CAPEX detecte : 1 129 667 152 FCFA
- Score qualite IA : 0.96
- Aucun `CODE_BPU` orphelin

La simulation CAPEX locale retourne :

- CAPEX brut : 1 129 667 152 FCFA
- CAPEX import : 1 017 883 558 FCFA
- CAPEX optimise : 998 050 922 FCFA
- Economie nette : 131 616 230 FCFA
- Taux economie : 11.65 %
- Lignes import : 412
- Lignes local : 172

## Dataset officiel immutable

Fichiers :

- `03_DONNEES_REFERENCE/SP2I_CAPEX_DEMO_V1.xlsx`
- `03_DONNEES_REFERENCE/DATASET_METADATA.json`
- `03_DONNEES_REFERENCE/README_DATASET.md`

Role :

- dataset officiel de demonstration
- dataset QA
- dataset cloud par defaut
- source de seed PostgreSQL
- source de validation cockpit React et Analytics Engine V1

## Seed PostgreSQL

Script cree :

`07_API_BACKEND/app/scripts/seed_database.py`

Commande dry-run :

```bash
python 07_API_BACKEND/app/scripts/seed_database.py
```

Commande d'ecriture PostgreSQL :

```bash
python 07_API_BACKEND/app/scripts/seed_database.py --yes
```

Le script :

- charge `SP2I_CAPEX_DEMO_V1.xlsx`
- verifie le schema PostgreSQL
- nettoie le cache analytics
- execute le pipeline Excel -> PostgreSQL
- remplace `fact_metre`
- verifie les lignes, lots, CAPEX et economies

Sortie attendue apres seed :

```text
[OK] Dataset chargé
[OK] 584 lignes FACT_METRE
[OK] 14 lots détectés
[OK] CAPEX : 1 129 667 152
[OK] Economie : 131 616 230
[OK] Analytics views rebuilt
[OK] Seed completed
```

## Endpoint QA ajoute

Endpoint :

`/analytics/qa-summary`

Objectif :

- etat moteur analytics
- etat cache
- etat PostgreSQL
- coherence KPI
- readiness ECharts
- readiness AG Grid
- validation dataset cible

## Endpoints analytics testes en cloud

Base testee :

`https://sp2i-backend.onrender.com`

Resultat observe avant redeploiement du dernier commit backend :

| Endpoint | HTTP | API status | Temps | Donnees |
| --- | ---: | --- | ---: | --- |
| `/analytics/dashboard` | 200 | SUCCESS | 2269 ms | 153 lignes, CAPEX 6 297 157 385.68 |
| `/analytics/capex` | 200 | SUCCESS | 797 ms | 153 lignes, CAPEX 6 297 157 385.68 |
| `/analytics/heatmap` | 200 | SUCCESS | 1212 ms | chart OK |
| `/analytics/risk` | 200 | SUCCESS | 757 ms | chart OK |
| `/analytics/procurement` | 200 | SUCCESS | 627 ms | 153 lignes |
| `/analytics/logistics` | 200 | SUCCESS | 635 ms | 153 lignes |
| `/analytics/scenarios` | 200 | SUCCESS | 516 ms | 25 lignes |
| `/analytics/drilldown` | 200 | SUCCESS | 811 ms | chart OK |
| `/analytics/timeline` | 200 | SUCCESS | 808 ms | chart OK |
| `/analytics/system-health` | 200 | SUCCESS | 513 ms | moteur OK |
| `/analytics/qa-summary` | 404 | non deployee | 560 ms | endpoint ajoute dans le commit courant |

Conclusion cloud :

- Render repond correctement.
- Les endpoints analytics existants sont stables.
- La base cloud n'est pas encore alimentee par `SP2I_CAPEX_DEMO_V1`.
- Le cloud expose actuellement un ancien dataset de 153 lignes.
- Apres redeploiement puis seed, `/analytics/qa-summary` doit passer de 404 a SUCCESS.

## Validation attendue apres seed cloud

Apres execution du seed sur Render/PostgreSQL :

- `/analytics/kpis`
  - `capex_brut` = 1 129 667 152
  - `nb_lignes` = 584
  - `economie_nette` > 0

- `/analytics/dashboard`
  - KPI non nuls
  - charts `bar`, `heatmap`, `timeline` non vides
  - table AG Grid non vide

- `/analytics/qa-summary`
  - `metadata.qa_status` = `PASS`
  - `checks.nb_lignes_gt_500` = true
  - `checks.capex_brut_gt_0` = true
  - `checks.charts_ready` = true
  - `checks.ag_grid_ready` = true

## Script de validation automatique

Script cree :

`07_API_BACKEND/app/scripts/validate_analytics.py`

Commande :

```bash
python 07_API_BACKEND/app/scripts/validate_analytics.py --base-url https://sp2i-backend.onrender.com
```

Avec export JSON :

```bash
python 07_API_BACKEND/app/scripts/validate_analytics.py --base-url https://sp2i-backend.onrender.com --output docs/analytics_cloud_check.json
```

## Points detectes

### 1. Cloud non seedé avec V1

Le cloud retourne actuellement 153 lignes au lieu de 584.

Action :

1. redeployer backend avec le commit contenant `seed_database.py` et `/analytics/qa-summary`
2. executer le seed PostgreSQL avec `--yes`
3. relancer `validate_analytics.py`

### 2. QA endpoint non encore deployé

`/analytics/qa-summary` retourne 404 en cloud avant redeploiement.

Action :

Pousser le commit et attendre Render.

### 3. Validation destructive volontairement non lancee localement

Le seed PostgreSQL avec `--yes` remplace `fact_metre`. Il n'a pas ete execute sans confirmation explicite sur une base cloud.

## Recommandation de validation finale

Ordre recommande :

1. Commit + push des fichiers QA.
2. Attendre redeploiement Render.
3. Executer sur Render :

```bash
python 07_API_BACKEND/app/scripts/seed_database.py --yes
```

4. Tester :

```bash
python 07_API_BACKEND/app/scripts/validate_analytics.py --base-url https://sp2i-backend.onrender.com
```

5. Ouvrir le frontend Vercel.
6. Verifier Cockpit Direction, Analytics, Drill-down et DQE.

## Statut final actuel

Statut local :

`PASS`

Statut cloud :

`WARN - backend stable mais dataset V1 non seedé`

Statut production analytics validation :

`pret pour seed cloud`
