# Audit Power BI - 02_ANALYSE_COUTS

## Diagnostic

Le symptome `(Vide)` sur les KPI CAPEX avec des filtres comme `BAT_01 / N2 / A201 / SEJOUR / LOT ELECTRICITE` est coherent avec un probleme de segment dimensionnel.

La surface reste renseignee parce qu'elle provient des dimensions spatiales, alors que les KPI CAPEX proviennent de `fact_metre`. Si le segment Lot selectionne une valeur presente dans `dim_lot` mais absente de `fact_metre`, le contexte filtre les faits a zero ligne et les mesures CAPEX retournent vide ou 0 selon leur robustesse.

Cause probable :

- `dim_lot` contient deux generations de lots.
- Les anciens lots (`LOT ELECTRICITE`, `LOT TECHNIQUE`, `LOT 1`, `LOT 4`, `LOT 6`) polluent les segments.
- `fact_metre` est alimente avec les nouveaux codes BIM (`LOT_ELEC`, `LOT_CVC`, `LOT_CAR`, `LOT_FP`, `LOT_PNT`, `LOT_SOL`, `LOT_TOIT`).

## Requetes SQL

Les requetes d'audit sont dans :

```text
06_ANALYSE_BI/MPEMBA_V2/02_analyse_couts_audit.sql
```

Elles couvrent :

- lots de `fact_metre`
- lots de `dim_lot`
- lots dimensionnels jamais utilises
- lots fact absents de dimension
- coherence sous-lots
- coherence articles
- controle des vues actives

## Correctif SQL applique

Trois vues propres sont ajoutees au script Power BI :

```text
vw_dim_lot_active
vw_dim_sous_lot_active
vw_dim_article_bpu_active
```

Elles ne retournent que les membres dimensionnels reellement presents dans `fact_metre`.

## Correctif Power BI recommande

Dans Power Query V2 :

- `DimLot` lit maintenant `vw_dim_lot_active`
- `DimSousLotComplet` lit maintenant `vw_dim_sous_lot_active`
- `DimArticleBpu` lit maintenant `vw_dim_article_bpu_active`

Les noms de tables Power BI restent identiques pour limiter la casse des visuels.

## Relations a verifier

Relations attendues :

```text
DimLot[lot]                         1 -> * FactMetre[lot]
DimSousLotComplet[sous_lot_id]      1 -> * FactMetre[sous_lot_id]
DimArticleBpu[code_article]         1 -> * FactMetre[code_article]
```

Toutes les relations doivent etre :

- cardinalite `1 -> *`
- direction unique
- non bidirectionnelles
- non Many-to-Many

Si le modele contient encore une relation `dim_lot[lot_id] -> fact_metre[lot_id]` et que `fact_metre[lot_id]` contient des codes texte BIM alors que `dim_lot[lot_id]` est numerique ou historique, supprimer cette relation et utiliser `lot`.

## Visuels a auditer dans 02_ANALYSE_COUTS

Verifier les visuels suivants :

- CAPEX par lot
- CAPEX par sous-lot
- CAPEX par article
- CAPEX par appartement
- KPI CAPEX Local
- KPI CAPEX Import
- KPI CAPEX Optimise
- KPI Economie
- KPI CAPEX/m2

Controle visuel :

- aucun filtre visuel cache sur ancien lot
- aucun Top N sans mesure robuste
- interactions activees depuis les slicers principaux
- aucun filtre de page conserve depuis V1
- aucun champ provenant de `v_kpi_*`

## Mesures durcies

Les mesures DAX V2 ont ete durcies :

- `COALESCE(SUM(...),0)` pour les sommes
- `DIVIDE(...,...,0)` pour les ratios
- `COALESCE(AVERAGEX(...),0)` pour les moyennes

Cela evite les `(Vide)` techniques. Attention : si le contexte filtre vraiment zero ligne de `fact_metre`, le KPI affichera `0`, ce qui doit etre accompagne d'un indicateur `Nb lignes` dans la page.

## Option de nettoyage

Option recommandee : C.

Conserver l'historique dans `dim_lot`, mais utiliser `vw_dim_lot_active` dans Power BI pour les segments.

Options alternatives :

- A : supprimer les anciens lots non utilises. Plus radical, risque de perdre l'historique V1.
- B : conserver les anciens lots et les masquer manuellement dans les segments. Fragile apres refresh.

## Validation attendue

Apres correction :

1. Rafraichir les vues Neon avec `sql/powerbi/001_powerbi_views.sql`.
2. Rafraichir Power BI en mode Import.
3. Verifier que les segments Lot n'affichent plus les lots historiques non utilises.
4. Tester :

```text
BAT_01
N2
A201
SEJOUR
LOT_ELEC
```

5. Les KPI CAPEX doivent afficher des montants si `fact_metre` contient des lignes.
6. Tester l'ancien filtre `LOT ELECTRICITE` : il ne doit plus etre disponible dans le segment actif, ou il doit donner explicitement 0 ligne.

## Risque residuel

Le risque residuel principal est une relation Power BI encore basee sur une mauvaise cle ou une interaction de visuel desactivee dans le fichier `.pbix`. Ce point ne peut pas etre corrige par SQL seul : il doit etre verifie dans la vue Modele et dans le panneau Filtres Power BI.

