# Strategie de Densite Dashboard

## Objectif

SP2I doit etre dense comme un outil decisionnel, mais pas illisible. La densite
doit servir la decision, pas remplir l'ecran.

## Regle 5-2-1

```text
5 KPI maximum
2 visualisations principales maximum
1 table principale maximum
```

Si une page depasse cette regle, le contenu doit passer dans :

- tabs
- drawer
- accordions
- panneaux secondaires
- Power BI

## Hierarchie visuelle

### Niveau 1 : decision

Ce qui doit etre visible sans scroll :

- CAPEX local
- CAPEX optimise
- economie
- risque global
- scenario actif
- alerte critique

### Niveau 2 : explication

Accessible dans la meme page :

- pourquoi la decision est prise
- quelles lignes sont sensibles
- quels lots sont critiques
- quels risques expliquent le score

### Niveau 3 : detail

Accessible par drawer ou Power BI :

- historique complet
- logs pipeline
- detail fournisseur
- detail container
- detail ligne DQE

## KPI cards

Une KPI card doit contenir :

```text
Label court
Valeur
Tendance ou statut
Couleur semantique discrete
```

Eviter :

- descriptions longues
- icones decoratives inutiles
- plus de 5 KPI par ligne
- couleurs trop nombreuses

## Tables

Les tables doivent etre utiles pour agir.

Recommandations :

- Colonnes prioritaires a gauche.
- Colonnes techniques masquables.
- Ligne cliquable -> drawer detail.
- Header sticky dans le panneau.
- Scroll interne a la table.

Colonnes prioritaires simulation :

```text
Designation
Lot
CAPEX local
CAPEX optimise
Economie
Decision
Risque
Action
```

## Charts

React doit afficher des charts rapides pour l'operationnel. Power BI garde les
dashboards analytiques profonds.

Charts React recommandes :

- barres simples CAPEX par lot
- heatmap risque chantier
- timeline ETA
- mini tendance scenarios

Charts a laisser a Power BI :

- drilldown financier complet
- matrices multi-dimensions
- analyses temporelles avancees
- decompositions complexes

## Progressive disclosure

Ne pas montrer tout en meme temps.

Exemple Simulation :

```text
Vue principale :
    KPI + table lignes critiques

Clic ligne :
    drawer explication decision

Tab secondaire :
    toutes les lignes

Power BI :
    analyse globale direction
```

## Densite par ecran

### Laptop

Objectif : tout le pilotage principal doit tenir en 768-900 px de hauteur.

### Desktop

Objectif : utiliser split-screen et panneau lateral.

### Ultrawide

Objectif : ajouter un troisieme panneau utile, pas etirer les cards.

### Mobile chantier

Objectif : afficher seulement actions et alertes.

