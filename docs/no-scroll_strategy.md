# Strategie No-Scroll SP2I

## Principe

Le scroll global est l'ennemi d'un cockpit. Il fait perdre le contexte, cache les
KPI et ralentit les actions. SP2I doit privilegier des zones fixes et des scrolls
locaux.

## Probleme a eviter

```text
Header
KPI
Chart
Chart
Table
Details
Actions
Footer
```

Ce modele produit une page longue et une perte de contexte.

## Modele cible

```text
Viewport complet
    topbar fixe
    sidebar fixe
    page header compact
    KPI fixes
    zone centrale scrollable localement
    drawer details
```

## Regles pratiques

1. `body` ne doit pas etre le conteneur de scroll principal dans `/app`.
2. `.content-area` peut occuper le viewport restant.
3. Chaque table doit avoir son propre conteneur scrollable.
4. Les cards secondaires doivent passer dans des tabs.
5. Les details doivent aller en drawer.

## Hauteurs recommandees

```text
Topbar               64-72 px
Header page          80-120 px
KPI strip            96-120 px
Tabs                 40-48 px
Zone centrale        hauteur restante
```

## Patterns par page

### Simulation

```text
No-scroll global
Table simulation scroll interne
Panneau parametres sticky
Drawer explication decision
```

### DQE

```text
Preview table scroll interne
Mapping panel sticky
Anomalies en tab
```

### Analytics

```text
Un seul Power BI embed
Dashboard selector horizontal
Pas de grille de 7 iframes
```

### Logistics

```text
Tabs containers / shipments / freight / site
Table active scroll interne
Details shipment en drawer
```

## Desktop CSS cible

Exemple conceptuel :

```css
.saas-shell {
  height: 100vh;
  overflow: hidden;
}

.saas-main {
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
}

.content-area {
  min-height: 0;
  overflow: hidden;
}

.cockpit-page {
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
}

.panel-scroll {
  min-height: 0;
  overflow: auto;
}
```

## Responsive

Sur mobile, le no-scroll strict est moins realiste. Il faut passer a une logique
task-first :

```text
Alertes
Livraisons
Actions
Validation
```

Le cockpit complet reste prioritaire sur desktop et tablette.

