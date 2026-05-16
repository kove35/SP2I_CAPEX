# Strategie Navigation SP2I CAPEX

## Principe directeur

La navigation SP2I doit raconter le pilotage immobilier, pas l'organisation
technique du code. L'utilisateur ne doit pas penser "routes React", mais :

```text
Je pilote mon projet
Je controle mon CAPEX
Je structure mon DQE
Je compare mes scenarios
Je suis mes risques
Je consulte mes dashboards
```

## Navigation cible

Conserver peu de routes principales :

```text
/app                 Cockpit
/app/simulation      Investissements & CAPEX
/app/dqe             DQE & Data
/app/site            Pilotage Projet
/app/procurement     Procurement & Supply Chain
/app/analytics       Analytics Power BI
```

## Architecture recommandee

```text
Sidebar principale
    -> modules stables

Tabs internes
    -> vues metier dans un module

Drawer details
    -> informations secondaires

Topbar
    -> contexte projet / scenario / alertes
```

## Probleme actuel

La sidebar liste beaucoup de sous-entrees, mais plusieurs pointent vers la meme
route. C'est acceptable techniquement, mais ambigu en UX.

Exemple :

```text
Planning
Dependances
Livraisons
Criticite
Suivi chantier
```

Ces entrees doivent piloter un etat interne de la page `/app/site`.

## Modele de navigation recommande

### Sidebar

La sidebar doit contenir :

```text
Cockpit
Investissements & CAPEX
DQE & Data
Pilotage Projet
Procurement & Supply Chain
Analytics Power BI
Administration
```

### Sous-navigation interne

Dans chaque page :

```text
Investissements & CAPEX
    [Simulation] [Scenarios] [Historique] [Comparaison]

DQE & Data
    [Import] [Analyse] [Mapping] [Qualite] [Anomalies]

Pilotage Projet
    [Planning] [Dependances] [Livraisons] [Criticite] [Stockage]

Procurement & Supply Chain
    [Fournisseurs] [Import] [Cashflow] [MOQ] [Risques]

Analytics Power BI
    [Direction] [CAPEX] [Projet] [Procurement] [Logistics] [Risks]
```

## Clics cibles

| Action critique | Cible UX |
| --- | --- |
| Lancer une simulation | 1 clic depuis Cockpit ou Simulation |
| Importer un DQE | 1 clic depuis topbar ou DQE |
| Comparer scenarios | 2 clics maximum |
| Voir dashboard direction | 1 clic depuis topbar ou Analytics |
| Ouvrir alertes critiques | 1 clic topbar |
| Comprendre une decision | 1 clic sur ligne simulation |

## Quick actions

Ajouter une zone d'actions rapides, visible dans la sidebar ou topbar :

```text
+ Importer DQE
+ Lancer simulation
+ Comparer scenarios
+ Ouvrir Power BI
```

Ces actions reduisent fortement la friction.

## Sidebar enterprise

La sidebar ideale :

```text
┌ SP2I CAPEX ──────────────┐
│ Projet: Pointe-Noire     │
├──────────────────────────┤
│ Cockpit                  │
│ CAPEX                    │
│ DQE                      │
│ Projet                   │
│ Procurement              │
│ Analytics                │
├──────────────────────────┤
│ + Importer DQE           │
│ + Simulation             │
│ + Power BI               │
└──────────────────────────┘
```

## Administration

Administration ne doit pas etre cachee dans Analytics. Elle doit etre separee
ou placee en bas de sidebar.

Recommandation :

```text
Administration
    Parametres
    Utilisateurs
    Connecteurs
    Power BI
```

## Roadmap navigation

### V1

- Garder les routes actuelles.
- Remplacer les sous-menus dupliques par des tabs internes.
- Ajouter quick actions.

### V2

- Ajouter navigation contextuelle par module.
- Ajouter recherche globale.
- Ajouter drawer d'alertes.

### V3

- Ajouter raccourcis clavier.
- Ajouter favoris utilisateur.
- Ajouter historique de navigation projet/scenario.

