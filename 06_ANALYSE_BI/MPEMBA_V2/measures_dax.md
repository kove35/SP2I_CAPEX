# Mesures DAX - SP2I CAPEX MPEMBA V2

Creer une table vide `Mesures SP2I`, puis ranger les mesures dans les dossiers indiques.

## _KPI_DIRECTION

```DAX
CAPEX Total =
COALESCE ( SUM ( fact_metre[capex_local] ), 0 )
```

```DAX
CAPEX Local =
COALESCE ( SUM ( fact_metre[capex_local] ), 0 )
```

```DAX
CAPEX Optimise =
COALESCE ( SUM ( fact_metre[capex_optimise] ), 0 )
```

```DAX
CAPEX Import =
COALESCE ( SUM ( fact_metre[capex_import] ), 0 )
```

```DAX
Economie =
COALESCE ( SUM ( fact_metre[economie] ), 0 )
```

```DAX
Taux Economie =
DIVIDE ( [Economie], [CAPEX Total], 0 )
```

```DAX
Surface Totale =
COALESCE ( SUM ( dim_piece[surface_m2] ), 0 )
```

```DAX
CAPEX/m2 =
DIVIDE ( [CAPEX Optimise], [Surface Totale], 0 )
```

```DAX
Nb Batiments =
COALESCE ( DISTINCTCOUNT ( dim_batiment[batiment_id] ), 0 )
```

```DAX
Nb Niveaux =
COALESCE ( DISTINCTCOUNT ( dim_niveau[niveau_id] ), 0 )
```

```DAX
Nb Appartements =
COALESCE ( DISTINCTCOUNT ( dim_appartement[appartement_id] ), 0 )
```

```DAX
Nb Pieces =
COALESCE ( DISTINCTCOUNT ( dim_piece[piece_id] ), 0 )
```

```DAX
Nb Lots =
COALESCE ( DISTINCTCOUNT ( dim_lot[lot_id] ), 0 )
```

```DAX
Nb Sous-lots =
COALESCE ( DISTINCTCOUNT ( dim_sous_lot_complet[sous_lot_id] ), 0 )
```

```DAX
Nb Articles =
COALESCE ( DISTINCTCOUNT ( dim_article_bpu[code_article] ), 0 )
```

## _KPI_COST_INTELLIGENCE

```DAX
Rang CAPEX Article =
RANKX (
    ALLSELECTED ( dim_article_bpu[code_article] ),
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
        ALLSELECTED ( dim_article_bpu[code_article] ),
        [Rang CAPEX Article] <= CurrentRank
    ),
    [CAPEX Optimise]
)
```

```DAX
Pareto % Article =
DIVIDE ( [CAPEX Cumul Article], CALCULATE ( [CAPEX Optimise], ALLSELECTED ( dim_article_bpu[code_article] ) ), 0 )
```

```DAX
Article Pareto 80 =
IF ( [Pareto % Article] <= 0.8, 1, 0 )
```

```DAX
CAPEX Appartement Moyen =
COALESCE ( AVERAGEX ( VALUES ( dim_appartement[appartement_id] ), [CAPEX Optimise] ), 0 )
```

```DAX
Ecart CAPEX Appartement =
[CAPEX Optimise] - [CAPEX Appartement Moyen]
```

```DAX
CAPEX Piece Moyen =
COALESCE ( AVERAGEX ( VALUES ( dim_piece[piece_id] ), [CAPEX Optimise] ), 0 )
```

```DAX
CAPEX Piece Ecart =
[CAPEX Optimise] - [CAPEX Piece Moyen]
```

```DAX
CAPEX/m2 Moyen Piece =
COALESCE ( AVERAGEX ( VALUES ( dim_piece[piece_id] ), [CAPEX/m2] ), 0 )
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
COALESCE ( CALCULATE ( [CAPEX Optimise], fact_metre[decision_import] = "IMPORT" ), 0 )
```

```DAX
CAPEX Local Retenu =
COALESCE ( CALCULATE ( [CAPEX Optimise], fact_metre[decision_import] = "LOCAL" ), 0 )
```

```DAX
CAPEX Hybride =
COALESCE ( CALCULATE ( [CAPEX Optimise], fact_metre[decision_import] = "HYBRIDE" ), 0 )
```

```DAX
ROI Import =
DIVIDE ( [Economie], [CAPEX Importable], 0 )
```

```DAX
Part Import =
DIVIDE ( [CAPEX Importable], [CAPEX Optimise], 0 )
```

```DAX
Part Local =
DIVIDE ( [CAPEX Local Retenu], [CAPEX Optimise], 0 )
```

## _KPI_RISK

```DAX
Nb Lignes Risque =
COALESCE ( COUNTROWS ( FILTER ( fact_metre, NOT ISBLANK ( fact_metre[risque] ) ) ), 0 )
```

```DAX
Risque Moyen =
COALESCE ( AVERAGE ( fact_metre[risque] ), 0 )
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
COALESCE ( CALCULATE ( [CAPEX Optimise], FILTER ( fact_metre, fact_metre[risque] >= 60 ) ), 0 )
```

```DAX
Part CAPEX A Risque =
DIVIDE ( [CAPEX A Risque], [CAPEX Optimise], 0 )
```
