# Architecture Cockpit SP2I

## Vision

SP2I doit fonctionner comme une tour de controle immobiliere. Le cockpit ne doit
pas empiler les pages : il doit garder le contexte, montrer les priorites et
permettre d'agir vite.

## Grille cockpit standard

```text
┌──────────────────────────────────────────────────────────────────┐
│ Topbar : projet | scenario | risque | alertes | actions rapides  │
├───────────────┬──────────────────────────────────────────────────┤
│ Sidebar       │ Page header compact                              │
│ modules       ├──────────────────────────────────────────────────┤
│               │ KPI strip                                        │
│               ├────────────────────────────┬─────────────────────┤
│               │ Zone principale             │ Panneau contexte    │
│               │ table / chart / workflow    │ details / alerts    │
│               │ scroll interne si besoin    │ actions             │
└───────────────┴────────────────────────────┴─────────────────────┘
```

## Regles de conception

1. Une page = une mission metier.
2. Une table principale maximum par page.
3. Les details ne changent pas de page : ils s'ouvrent en drawer.
4. Les KPI restent visibles au-dessus de la zone de travail.
5. Power BI est integre comme espace analytique, pas comme copie React.

## Page Cockpit global

Mission :

```text
Donner l'etat du projet en moins de 10 secondes.
```

Visible immediatement :

- CAPEX local
- CAPEX optimise
- economie
- risque global
- scenario actif
- alertes critiques
- prochaines actions

Layout recommande :

```text
Header compact
KPI strip 5 cards
Left: flux DQE -> Simulation -> Decision -> Power BI
Right: alertes et actions
Bottom: mini timeline chantier
```

## Page CAPEX & Simulation

Mission :

```text
Simuler, arbitrer et comparer.
```

Layout recommande :

```text
Tabs: Simulation | Scenarios | Historique | Comparaison
KPI strip
Split screen:
    gauche: lignes simulation
    droite: parametres, decision summary, warnings
Drawer: explication ligne
```

## Page DQE & Data

Mission :

```text
Transformer un fichier source en donnees fiables.
```

Layout recommande :

```text
Left panel: upload + fichier actif
Center: table preview
Right panel: qualite, mapping, anomalies
Bottom tabs: lots | familles | lignes rejetees | lineage
```

## Page Pilotage Projet

Mission :

```text
Relier les decisions CAPEX au chantier.
```

Layout recommande :

```text
Tabs: Planning | Dependances | Livraisons | Criticite | Stockage
KPI strip chantier
Main: timeline / liste priorisee
Right: alertes chantier
```

## Page Procurement & Supply Chain

Mission :

```text
Optimiser sans voler la vedette au pilotage immobilier.
```

Layout recommande :

```text
Tabs: Fournisseurs | Import | Cashflow | MOQ | Risques
KPI strip optimisation
Main: decisions procurement
Right: risque / lead time / cashflow
```

## Page Analytics Power BI

Mission :

```text
Analyser en profondeur sans recalculer dans React.
```

Layout recommande :

```text
Dashboard selector compact
Power BI embed unique
Context bar: projet / scenario / periode
Right drawer: notes, filtres metier, liens cockpit
```

## Multi-panels recommandes

| Page | Pattern |
| --- | --- |
| Simulation | split-screen + drawer |
| DQE | three-panel validation |
| Site | tabs + timeline + alerts |
| Procurement | tabs + decision panel |
| Logistics | tabs + table/details |
| Analytics | dashboard selector + single embed |

## Mode dense

Pour un cockpit enterprise, prevoir un mode dense :

- KPI cards plus basses.
- Headers de page reduits.
- Tables avec lignes compactes.
- Sidebar collapsible.
- Panels resizables plus tard.

