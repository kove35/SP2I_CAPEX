# Mesures DAX - SP2I CAPEX MPEMBA V2

Creer une table vide `Mesures SP2I`, puis ranger les mesures dans les dossiers indiques.

## _KPI_DIRECTION

```DAX
CAPEX Total =
SUM ( fact_metre[capex_local] )
```

```DAX
CAPEX Local =
SUM ( fact_metre[capex_local] )
```

```DAX
CAPEX Optimise =
SUM ( fact_metre[capex_optimise] )
```

```DAX
CAPEX Import =
SUM ( fact_metre[capex_import] )
```

```DAX
Economie =
SUM ( fact_metre[economie] )
```

```DAX
Taux Economie =
DIVIDE ( [Economie], [CAPEX Total] )
```

```DAX
Surface Totale =
SUM ( dim_piece[surface_m2] )
```

```DAX
CAPEX/m2 =
DIVIDE ( [CAPEX Optimise], [Surface Totale] )
```

```DAX
Nb Batiments =
DISTINCTCOUNT ( dim_batiment[batiment_id] )
```

```DAX
Nb Niveaux =
DISTINCTCOUNT ( dim_niveau[niveau_id] )
```

```DAX
Nb Appartements =
DISTINCTCOUNT ( dim_appartement[appartement_id] )
```

```DAX
Nb Pieces =
DISTINCTCOUNT ( dim_piece[piece_id] )
```

```DAX
Nb Lots =
DISTINCTCOUNT ( dim_lot[lot_id] )
```

```DAX
Nb Sous-lots =
DISTINCTCOUNT ( dim_sous_lot_complet[sous_lot_id] )
```

```DAX
Nb Articles =
DISTINCTCOUNT ( dim_article_bpu[article_id] )
```

## _KPI_COST_INTELLIGENCE

```DAX
Rang CAPEX Article =
RANKX (
    ALLSELECTED ( dim_article_bpu[article_id] ),
    [CAPEX Optimise],
    ,
    DESC,
    Dense
)
```

```DAX
CAPEX Cumul Article =
VAR CurrentRank = [Rang CAPEX Article]
RETURN
SUMX (
    FILTER (
        ALLSELECTED ( dim_article_bpu[article_id] ),
        [Rang CAPEX Article] <= CurrentRank
    ),
    [CAPEX Optimise]
)
```

```DAX
Pareto % Article =
DIVIDE ( [CAPEX Cumul Article], CALCULATE ( [CAPEX Optimise], ALLSELECTED ( dim_article_bpu[article_id] ) ) )
```

```DAX
Article Pareto 80 =
IF ( [Pareto % Article] <= 0.8, 1, 0 )
```

```DAX
CAPEX Appartement Moyen =
AVERAGEX ( VALUES ( dim_appartement[appartement_id] ), [CAPEX Optimise] )
```

```DAX
Ecart CAPEX Appartement =
[CAPEX Optimise] - [CAPEX Appartement Moyen]
```

```DAX
CAPEX Piece Moyen =
AVERAGEX ( VALUES ( dim_piece[piece_id] ), [CAPEX Optimise] )
```

```DAX
CAPEX Piece Ecart =
[CAPEX Optimise] - [CAPEX Piece Moyen]
```

```DAX
CAPEX/m2 Moyen Piece =
AVERAGEX ( VALUES ( dim_piece[piece_id] ), [CAPEX/m2] )
```

```DAX
CAPEX/m2 Ecart Piece =
[CAPEX/m2] - [CAPEX/m2 Moyen Piece]
```

```DAX
Anomalie CAPEX/m2 =
VAR AvgCapexM2 =
    AVERAGEX ( ALLSELECTED ( dim_piece[piece_id] ), [CAPEX/m2] )
VAR StdCapexM2 =
    STDEVX.S ( ALLSELECTED ( dim_piece[piece_id] ), [CAPEX/m2] )
RETURN
IF (
    NOT ISBLANK ( [CAPEX/m2] )
        && StdCapexM2 > 0
        && ABS ( [CAPEX/m2] - AvgCapexM2 ) > 2 * StdCapexM2,
    1,
    0
)
```

```DAX
Criticite Anomalie =
VAR AvgCapexM2 =
    AVERAGEX ( ALLSELECTED ( dim_piece[piece_id] ), [CAPEX/m2] )
VAR StdCapexM2 =
    STDEVX.S ( ALLSELECTED ( dim_piece[piece_id] ), [CAPEX/m2] )
VAR Delta =
    ABS ( [CAPEX/m2] - AvgCapexM2 )
RETURN
SWITCH (
    TRUE (),
    ISBLANK ( [CAPEX/m2] ) || StdCapexM2 = 0, "NORMAL",
    Delta > 3 * StdCapexM2, "HIGH",
    Delta > 2 * StdCapexM2, "MEDIUM",
    "NORMAL"
)
```

## _KPI_PROCUREMENT

```DAX
CAPEX Importable =
CALCULATE ( [CAPEX Optimise], fact_metre[decision_import] = "IMPORT" )
```

```DAX
CAPEX Local Retenu =
CALCULATE ( [CAPEX Optimise], fact_metre[decision_import] = "LOCAL" )
```

```DAX
CAPEX Hybride =
CALCULATE ( [CAPEX Optimise], fact_metre[decision_import] = "HYBRIDE" )
```

```DAX
ROI Import =
DIVIDE ( [Economie], [CAPEX Importable] )
```

```DAX
Part Import =
DIVIDE ( [CAPEX Importable], [CAPEX Optimise] )
```

```DAX
Part Local =
DIVIDE ( [CAPEX Local Retenu], [CAPEX Optimise] )
```

## _KPI_RISK

```DAX
Nb Lignes Risque =
COUNTROWS ( FILTER ( fact_metre, NOT ISBLANK ( fact_metre[risque] ) ) )
```

```DAX
Risque Moyen =
AVERAGE ( fact_metre[risque] )
```

```DAX
Top Risque CAPEX =
CALCULATE (
    [CAPEX Optimise],
    TOPN (
        10,
        ALLSELECTED ( fact_metre ),
        fact_metre[risque],
        DESC
    )
)
```

```DAX
CAPEX A Risque =
CALCULATE ( [CAPEX Optimise], FILTER ( fact_metre, fact_metre[risque] >= 60 ) )
```

```DAX
Part CAPEX A Risque =
DIVIDE ( [CAPEX A Risque], [CAPEX Optimise] )
```

