# Audit UX/UI Frontend SP2I CAPEX

## Objectif

Cet audit analyse le frontend SP2I comme un cockpit decisionnel immobilier enterprise.
Le but n'est pas de rendre l'interface plus decorative, mais de la rendre plus rapide,
plus dense, plus lisible et plus utile pour piloter des investissements immobiliers.

SP2I doit etre percu comme :

```text
Plateforme decisionnelle immobiliere
    -> pilotage CAPEX
    -> DQE intelligent
    -> scenarios
    -> risques
    -> chantier
    -> Power BI analytics
    -> moteurs d'optimisation procurement / supply chain / logistique
```

## Synthese executive

Le frontend actuel a une bonne base technique : un shell SaaS, une sidebar, une
topbar, des pages metier, des services API et une landing repositionnee sur le
pilotage immobilier. La principale dette UX vient maintenant de la structure
informationnelle : trop d'entrees de menu pointent vers les memes pages, les
pages sont encore pensees comme des empilements verticaux, et les workflows
metier ne sont pas assez regroupes dans des vues cockpit.

Priorites UX :

1. Transformer les sous-menus en onglets contextuels ou panneaux internes.
2. Limiter chaque page metier a un ecran principal visible sans scroll lourd.
3. Mettre les KPI, alertes et actions critiques dans une zone stable.
4. Utiliser Power BI comme espace analytique docke, pas comme rupture de contexte.
5. Reduire les routes principales a 6 cockpits utiles.

## Audit navigation globale

### Etat actuel

La sidebar expose les familles suivantes :

```text
Cockpit
Investissements & CAPEX
Pilotage Projet
DQE & Data
Procurement & Supply Chain
Analytics
```

Constat important : plusieurs boutons d'une meme section pointent vers la meme
route. Exemple :

```text
Planning       -> /app/site
Dependances    -> /app/site
Livraisons     -> /app/site
Criticite      -> /app/site
Suivi chantier -> /app/site
```

Ce choix garde peu de routes, ce qui est bon. Mais l'utilisateur pense cliquer
sur des pages differentes alors qu'il arrive au meme endroit. Il faut donc
assumer ce modele : ces entrees doivent devenir des ancres internes, des onglets
ou des filtres de contexte.

### Friction actuelle

Pour une action critique comme comparer deux scenarios, le chemin mental est :

```text
Sidebar -> Investissements & CAPEX -> Scenarios -> onglet Scenarios -> bouton Comparer
```

Ce n'est pas excessif, mais l'action n'est pas encore assez visible dans le
cockpit principal. Pour un cockpit enterprise, les actions critiques doivent
etre accessibles depuis :

```text
Cockpit global -> action rapide
Page metier -> action principale
Topbar -> contexte projet / scenario
```

### Recommandation

Conserver 6 destinations principales :

```text
/app                 Cockpit global
/app/simulation      CAPEX & scenarios
/app/dqe             DQE & data quality
/app/site            Pilotage projet
/app/procurement     Procurement & supply chain
/app/analytics       Power BI analytics
```

Puis deplacer les sous-menus dans chaque page comme des tabs horizontaux :

```text
Simulation page
    [Simulation] [Scenarios] [Historique] [Comparaison]

Site page
    [Planning] [Dependances] [Livraisons] [Criticite] [Stockage]

DQE page
    [Import Excel] [Analyse] [Normalisation] [Qualite]
```

## Audit des scrolls

### Risques constates

Les pages actuelles suivent souvent ce modele :

```text
Hero
KPI grid
Panel 1
Panel 2
Table
```

Sur desktop, cela reste acceptable aujourd'hui car les pages sont encore peu
chargees. Mais des que les tableaux, graphiques et modules Power BI seront reels,
le scroll vertical deviendra rapidement le probleme principal.

### Strategie no-scroll

Chaque page cockpit doit tenir dans une grille de viewport :

```text
Topbar fixe
Sidebar fixe
Page header compact
KPI strip fixe
Zone centrale scrollable localement
Panneau lateral contextuel
```

Le scroll global de page doit etre evite. Si une table ou un dashboard deborde,
seul le panneau concerne doit scroller.

Pattern recommande :

```text
┌─────────────────────────────────────────────────────────────┐
│ Topbar projet / scenario / alertes                          │
├──────────────┬──────────────────────────────────────────────┤
│ Sidebar      │ Header compact + actions                     │
│ fixe         ├──────────────────────────────────────────────┤
│              │ KPI strip                                    │
│              ├───────────────────────────────┬──────────────┤
│              │ Table / chart / workflow      │ Details      │
│              │ scroll interne                │ contexte     │
└──────────────┴───────────────────────────────┴──────────────┘
```

## Audit pages metier

### Cockpit

Points forts :

- Bonne orientation decisionnelle.
- KPI visibles immediatement.
- Workflow DQE -> Power BI clair.

Limites :

- Le cockpit ne propose pas encore assez d'actions directes.
- Les alertes sont textuelles et non priorisees.
- Le lien avec scenarios actifs et projet actif reste faible.

Recommandation :

Le cockpit doit devenir la page "command center" :

```text
Visible immediatement :
- CAPEX local
- CAPEX optimise
- economie globale
- scenario actif
- alertes critiques
- prochaines actions

Secondaire :
- details des lignes
- logs techniques
- historique complet
```

### Simulation

Points forts :

- Onglets simulation / scenarios deja presents.
- Toolbar metier existante.
- Table simulation raccordee au backend.

Limites :

- Le tableau risque de consommer toute la hauteur.
- La comparaison scenarios est trop separee de la simulation.
- Les parametres metier devraient etre dans un panneau lateral ou drawer.

Recommandation :

```text
SimulationPage
    Header compact
    KPI strip
    Layout split :
        gauche  -> table simulation
        droite  -> parametres + decision summary
    Bottom tabs :
        lignes / anomalies / comparaison / historique
```

### Procurement

Points forts :

- Agrege risk, lead time, cashflow et complexite.
- Bonne logique de moteur d'optimisation integre.

Limites :

- Tous les axes sont fusionnes dans une seule table.
- Il manque un panneau "decision procurement" clair.
- Le module ne doit pas reprendre le premier plan produit.

Recommandation :

Procurement doit etre un cockpit d'optimisation :

```text
Priorite :
- fournisseurs a risque
- decisions import/local a valider
- cashflow critique
- lead time critique

Secondaire :
- detail MOQ
- detail complexite
- historique fournisseur
```

### Logistics

Points forts :

- Separation containers / shipments.
- KPI simples et lisibles.

Limites :

- La logistique ne doit pas dominer l'UX globale.
- Manque de lien avec planning chantier.
- Les tables devraient etre en onglets ou panneaux dockes.

Recommandation :

```text
LogisticsPage
    [Containers] [Shipments] [Freight] [ETA chantier]
    Carte KPI compacte
    Tableau principal
    Panneau details shipment
```

### DQE

Points forts :

- Reutilise la page Import existante sans refactor brutal.

Limites :

- DQE est un module central pour SP2I, il merite une page cockpit dediee.
- L'utilisateur doit voir la qualite des donnees avant d'aller simuler.

Recommandation :

```text
DQEPage
    Upload / source file
    Score qualite
    Colonnes detectees
    Lots detectes
    Lignes rejetees
    Mapping propose
    Action : Envoyer vers simulation
```

### Pilotage Projet

Points forts :

- Message chantier coherent.
- KPI chantier simples.

Limites :

- Encore trop statique.
- Les sous-entrees de sidebar ne changent pas l'etat de page.

Recommandation :

Faire de `/app/site` une page multi-panels :

```text
Planning | Dependances | Livraisons | Criticite | Stockage
```

### Analytics

Points forts :

- Positionnement Power BI clair.
- React ne remplace pas Power BI.

Limites :

- Les dashboards sont actuellement des cards empilees.
- L'experience future Power BI doit eviter 7 iframes simultanees.

Recommandation :

Un seul embed Power BI visible a la fois, avec navigation dashboard compacte.

## Audit dashboard design

Regle de densite recommandee :

```text
Maximum 5 KPI primaires visibles.
Maximum 2 visualisations principales par ecran.
Maximum 1 table principale par page.
Details dans drawer, tabs ou drilldown.
```

Les KPI doivent etre classes :

```text
KPI de pilotage :
- CAPEX local
- CAPEX optimise
- economie totale
- risque global
- scenario actif

KPI d'optimisation :
- imports recommandes
- containers
- ETA moyen
- cashflow score

KPI techniques :
- lignes DQE
- lignes rejetees
- warnings
- temps traitement
```

## Audit workflows utilisateur

### Workflow CAPEX

Workflow cible :

```text
DQE -> Simulation -> Decision -> Validation -> Analytics
```

Regroupement recommande :

- DQE et Simulation doivent etre connectes par une action directe.
- Simulation et Decision doivent etre dans la meme page.
- Analytics Power BI doit s'ouvrir avec le meme projet et scenario actifs.

### Workflow Supply Chain

Workflow cible :

```text
Procurement -> Containers -> Shipment -> ETA -> Livraison chantier
```

Regroupement recommande :

- Procurement et Logistics peuvent rester separes.
- Le lien chantier doit etre visible dans les deux pages.
- Les details shipment doivent s'ouvrir en drawer, pas en nouvelle page.

### Workflow Projet

Workflow cible :

```text
Planning -> Criticite -> Risques -> Actions
```

Regroupement recommande :

- Planning, dependances et livraisons doivent etre dans un meme cockpit chantier.
- Les alertes critiques doivent remonter dans la topbar.

## Audit responsive

### Desktop standard

Le layout actuel est adapte. La sidebar 292px est confortable, mais un peu large
pour les laptops. Le mode collapsed est utile.

### Ultrawide

Risque : les grilles deviennent trop etirees. Utiliser des max-width internes
ou des colonnes dockees.

### Laptop

Priorite : reduire hero, KPI et padding. Les pages doivent tenir dans 900px de
hauteur autant que possible.

### Tablette

La sidebar doit devenir un rail compact ou drawer. Les tableaux doivent passer
en scroll interne horizontal controle.

### Mobile chantier

Ne pas chercher a reproduire le cockpit complet. Mode mobile = actions terrain :

```text
Alertes
Livraisons
ETA
Photos/documents
Validation rapide
```

## Audit performance UX

Risques :

- Appels API repetes dans plusieurs pages avec `simulateCapex`.
- Pas encore de cache de donnees.
- Pas de skeleton specifique par page.
- Les futures iframes Power BI peuvent alourdir fortement l'interface.

Recommandations :

- Introduire React Query quand les endpoints seront stabilises.
- Garder les tables virtualisables si plus de 500 lignes.
- Charger Power BI uniquement sur onglet actif.
- Prefetch leger des scenarios apres simulation.

## Audit topbar

La topbar actuelle montre projet, risque, containers et alertes. C'est une bonne
base, mais elle doit devenir le centre de contexte.

Topbar cible :

```text
Projet actif | Scenario actif | Statut DQE | Risque global | Alertes | Recherche | Actions rapides
```

Les alertes ne doivent pas seulement etre un compteur. Elles doivent ouvrir un
panel trie par severite.

## Audit sidebar

La sidebar est lisible, mais trop lineaire. Elle doit devenir plus contextuelle.

Recommendations :

- Garder les 6 sections principales.
- Transformer les sous-menus en raccourcis de tab interne.
- Ajouter 3 quick actions fixes :
  - Importer DQE
  - Lancer simulation
  - Ouvrir Power BI
- En mode collapsed, afficher tooltips.

## Priorisation

### Critique

1. Reduire la duplication des routes dans la sidebar.
2. Mettre en place des tabs internes par page.
3. Eviter le scroll global dans Simulation, Analytics et DQE.
4. Faire de la topbar la source du contexte projet/scenario.

### Important

1. Ajouter des drawers de details.
2. Introduire des panels scrollables localement.
3. Charger un seul dashboard Power BI a la fois.
4. Ajouter des quick actions metier.

### Amelioration

1. Transitions fluides.
2. Mode compact / dense.
3. Raccourcis clavier.
4. Favoris utilisateur.

