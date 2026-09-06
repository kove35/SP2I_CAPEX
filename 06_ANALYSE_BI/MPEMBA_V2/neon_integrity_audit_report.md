# Audit Neon - SP2I CAPEX MPEMBA V2

Date UTC : `2026-06-08T15:09:11.662303+00:00`
Base : `<NEON_DATABASE>`
Host : `<NEON_HOST>`
Neon : `True`

## Niveau de qualite : A

Objectif cible : A

## KPI SQL

```json
{
  "capex_local": 113928000.0,
  "capex_import": 107974967.99999996,
  "capex_optimise": 97174967.99999997,
  "economie": 16753032.0,
  "taux_economie": 0.14704929429113123,
  "surface_totale": 0.0,
  "surface_moyenne_appartement": 0.0,
  "capex_m2": 0.0
}
```

## FACT_METRE

Lignes : `290`

Montants :

```json
{
  "capex_local": 113928000.0,
  "capex_import": 107974967.99999996,
  "capex_optimise": 97174967.99999997,
  "economie": 16753032.0
}
```

Manquants :

```json
{
  "sans_lot": 0,
  "sans_sous_lot": 0,
  "sans_article": 0,
  "sans_batiment": 0,
  "sans_niveau": 0,
  "sans_appartement": 0,
  "sans_piece": 0
}
```

## Dimensions actives

```json
[
  {
    "view_name": "vw_dim_lot_active",
    "rows_count": 7,
    "distinct_count": 7
  },
  {
    "view_name": "vw_dim_sous_lot_active",
    "rows_count": 8,
    "distinct_count": 8
  },
  {
    "view_name": "vw_dim_article_bpu_active",
    "rows_count": 8,
    "distinct_count": 8
  }
]
```

## Tests de robustesse

```json
[
  {
    "batiment": "BAT_01",
    "niveau": "N1",
    "appartement": "A101",
    "piece": "CHAMBRE_1",
    "nb_lignes": 6,
    "capex_local": 2059500.0,
    "capex_optimise": 1721742.0,
    "economie": 337758.0
  },
  {
    "batiment": "BAT_01",
    "niveau": "N2",
    "appartement": "A201",
    "piece": "SEJOUR",
    "nb_lignes": 6,
    "capex_local": 4701000.0,
    "capex_optimise": 3930036.0,
    "economie": 770964.0
  },
  {
    "batiment": "BAT_01",
    "niveau": "N3",
    "appartement": "B301",
    "piece": "SDB_1",
    "nb_lignes": 6,
    "capex_local": 1062000.0,
    "capex_optimise": 887832.0,
    "economie": 174168.0
  },
  {
    "batiment": "BAT_01",
    "niveau": null,
    "appartement": null,
    "piece": null,
    "nb_lignes": 290,
    "capex_local": 113928000.0,
    "capex_optimise": 97174967.99999997,
    "economie": 16753032.0
  }
]
```

## Anomalies

- Aucune anomalie bloquante.

## Risques residuels

- Aucun risque residuel majeur detecte par l'audit SQL.

## Requetes correctives SQL

- Installer ou rafraichir les vues actives avec `sql/powerbi/001_powerbi_views.sql`.
- Utiliser `vw_dim_lot_active`, `vw_dim_sous_lot_active`, `vw_dim_article_bpu_active` dans Power BI.
- Si `vw_dim_article_bpu_active` est vide, aligner `fact_metre.code_article` avec `dim_article_bpu.code_article` ou charger `dim_article_bpu` depuis le master.
