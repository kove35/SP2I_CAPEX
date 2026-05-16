# Strategie Navigation Power BI dans SP2I

## Principe

Power BI reste le moteur analytics principal. React ne doit pas refaire les
dashboards, mais offrir le contexte operationnel et la navigation metier.

## Probleme a eviter

Ne pas afficher plusieurs dashboards Power BI en meme temps sous forme de cards.
Chaque iframe Power BI est lourde et cree une experience lente.

Mauvais modele :

```text
Dashboard Direction
Dashboard CAPEX
Dashboard Procurement
Dashboard Logistics
Dashboard Chantier
Dashboard Risks
```

sur une meme page verticale.

## Modele cible

```text
Analytics page
    dashboard selector
    context bar projet / scenario
    single Power BI embed
    drawer notes / filtres metier
```

## Navigation dashboard

Dashboards recommandes :

```text
Direction
CAPEX
Projet
Procurement
Logistics
Risks
Data Quality
```

Navigation sous forme de tabs ou segmented control :

```text
[Direction] [CAPEX] [Projet] [Procurement] [Logistics] [Risks]
```

## Contexte React -> Power BI

React doit transmettre :

- projet actif
- scenario actif
- periode active
- lot actif si selectionne
- niveau / batiment si selectionne

Power BI applique ces valeurs comme filtres.

## Contexte Power BI -> React

Quand l'utilisateur drilldown dans Power BI, React peut proposer :

- ouvrir la simulation correspondante
- ouvrir le scenario
- voir les lignes DQE
- ouvrir les alertes chantier

## Experience unifiee

```text
React cockpit
    -> action operationnelle
    -> simulation / validation
    -> lien "voir analyse"
    -> Power BI avec contexte deja filtre
```

## Performance

Recommandations :

1. Charger seulement le dashboard actif.
2. Eviter le rendu simultane de plusieurs embeds.
3. Afficher un skeleton analytics.
4. Memoriser le dernier dashboard ouvert.
5. Prevoir un etat "token expire" clair.

## UX cible

```text
┌─────────────────────────────────────────────────────────────┐
│ Analytics Power BI | Projet | Scenario | Periode            │
├─────────────────────────────────────────────────────────────┤
│ Direction | CAPEX | Projet | Procurement | Logistics | Risk │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Power BI Embedded                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Actions : Ouvrir simulation | Export | Commentaire         │
└─────────────────────────────────────────────────────────────┘
```

## Roadmap

### V1

- Remplacer les cards dashboard par un selecteur unique.
- Garder placeholders Power BI.

### V2

- Integrer Power BI Embedded avec configuration reportId/workspaceId.
- Appliquer projet/scenario actifs.

### V3

- Synchroniser drilldown Power BI vers React.
- Ajouter notes et snapshots decisionnels.

