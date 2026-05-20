# Audit optimisation CAPEX — Pointe-Noire

Date : 2026-05-19

## Contexte

SP2I_CAPEX est une plateforme SaaS enterprise de pilotage CAPEX immobilier. Le moteur actuel calcule :

- `CAPEX_LOCAL`
- `CAPEX_IMPORT`
- `ECONOMIE_NETTE`
- `TAUX_ECONOMIE_GLOBAL`

Le résultat observé pour Pointe-Noire (`122 707 910 FCFA`, `11 %`) est faible par rapport au potentiel réel d’import dans les lots concernés.

## 1. Audit du moteur actuel

### 1.1 Logique CAPEX existante

Le cœur du moteur se trouve dans `07_API_BACKEND/app/core/calculator.py` :

- `CAPEX_LOCAL` = `montant_local`
- `FOB_UNITAIRE` = `prix_fob` si fourni sinon `PU_LOCAL * ratio_famille * coefficient_risque`
- `IMPORT_UNITAIRE` = `FOB_UNITAIRE * (1 + somme(taux_landed_cost))`
- `CAPEX_IMPORT` = `IMPORT_UNITAIRE * quantite`
- `CAPEX_OPTIMISE` = `min(CAPEX_IMPORT, CAPEX_LOCAL)` avec choix `IMPORT` si `CAPEX_IMPORT < CAPEX_LOCAL * seuil_decision_import`
- `ECONOMIE_NETTE` = `CAPEX_LOCAL - CAPEX_OPTIMISE`

### 1.2 Fallback `PU_CHINE_FOB_E` → `PU_LOCAL`

Le fallback utilise un ratio fixe de `DEFAULT_RATIOS_FOB` et un coefficient risque `1.10`. Ce qui signifie :

- si `prix_fob` est absent, l’import est estimé sur `PU_LOCAL` et non sur un prix marché Chine réel;
- le ratio de 0.5 à 0.8 est conservateur et couvre mal des familles très importables comme `alucobond`, `menuiserie` ou `climatisation`;
- le coefficient de risque fixe écrase encore davantage le potentiel.

### 1.3 Impact des articles sans sourcing Chine

Les articles sans `prix_fob` tombent dans une estimation générique. Pour Pointe-Noire, cela masque :

- les coûts FOB Chine réels potentiellement plus bas que `PU_LOCAL * ratio`;
- la possibilité d’utiliser une base de fournisseurs China catalogue ;
- la valeur d’une logique de `source_confidence` plutôt qu’un ratio statique.

### 1.4 Impact des taux logistiques cumulés

Landed cost est une somme de taux fixes :

- transport maritime 15 %
- assurance 2 %
- douane 20 %
- frais portuaires 10 %
- logistique locale 5 %

Total = 52 %.

Ce niveau fixe est très pénalisant : il transforme un FOB chinois compétitif en un import souvent moins intéressant. Il ne reflète pas :

- la variation par nature d’article,
- le groupage/containerisation,
- la segmentation portuaire Chine → Pointe-Noire,
- les remises de fret FCL,
- l’externalisation des droits de douane spécifiques aux codes HS.

### 1.5 Impact du poids des lots non importables

Le calcul est entièrement ligne par ligne avec `decision = IMPORT|LOCAL`. Il ignore :

- le fait qu’un lot non importable peut rendre une importation associée non pertinente;
- la mutualisation des containers entre lots;
- les MOQ fournisseur/groupage;
- les contraintes projet (délai chantier, criticité).

### 1.6 Impact des hypothèses douane/transport

Le modèle ne calcule pas :

- un `importability_score` ou `logistics_risk` spécifique par famille;
- des délais en jours du port à chantier;
- des risques congestion portuaire ou supply chain Chine;
- une segmentation par port d’origine Chine.

### 1.7 Impact du calcul ligne par ligne

Le calcul ligne par ligne est simple et transparent, mais il casse deux leviers essentiels :

- optimisation multi-lots/container;
- arbitrage tarifaire entre lots proches ou mêmes fournisseurs.

### 1.8 Impact de la non mutualisation container

`ContainerEngine` existe, mais le moteur CAPEX n’intègre pas encore ses résultats au `CAPEX_IMPORT` ou à la décision.

- `ContainerEngine.evaluate()` calcule le mode FCL/LCL sur la base du volume d’une ligne.
- il ne regroupe pas plusieurs lignes pour optimiser le remplissage.

Conclusion : le moteur actuel sous-estime le potentiel parce qu’il applique des majorations logistiques conservatrices et des ratios FOB génériques sur chaque ligne isolée.

## 2. Analyse procurement

### 2.1 Sourcing coverage

Il faut distinguer 3 états pour chaque ligne :

- `Directement importable` : fournisseur Chine connu ou catégorie validée.
- `Indirectement importable` : besoin d’un RFQ / confirmation de MOQ.
- `Non importable` : réglementation, chantier, produit lourd ou spécifique local.

### 2.2 Import confidence score

La logique existante fixe un score de confiance simple dans `CalculateurCAPEX.scorer_confiance()`. Pour l’entreprise, il faut élargir à :

- `prix_fob` fourni et validé;
- `famille` clairement identifiée;
- `qualite_fournisseur` et certifications;
- `lead_time_days` attendu;
- `risk_level` global;
- `source_confidence` des bases fournisseurs.

### 2.3 Supplier maturity

Le parcours doit intégrer :

- maturation fournisseur Chine (`trust`, `history`, `capacity`);
- dépendance distribuant sur un petit nombre de fournisseurs;
- capacité à livrer la demande Pointe-Noire.

### 2.4 Procurement maturity

Proposer un score `PROCUREMENT MATURITY` calculé par :

- disponibilité des données sourcing;
- présence d’un `prix_fob` réel ou estimé par catégorie;
- niveau de conformité documentaire;
- couverture des risques logistiques/douaniers.

### 2.5 Hidden savings potential

Il faut évaluer le potentiel caché par :

- lots importables non retenus parce qu’un seuil de décision trop strict pénalise l’import;
- containers partiellement remplis qui ne voient pas l’effet de consolidation;
- articles dont `CAPEX_IMPORT` est proche de `CAPEX_LOCAL` mais qui deviennent rentables en mode `AGRESSIF`.

### 2.6 Optimisation par container

Prendre en compte :

- consolidation multi-lots pour FCL vs LCL;
- seuil de remplissage (`FCL_FILL_RATE_THRESHOLD`);
- coût par m3 variable selon mode;
- économies sur freight par volume.

### 2.7 Optimisation multi-lots

Un potentiel réel réside dans un regroupement des lignes :

- 1 container FCL peut absorber plusieurs lignes de `Menuiserie`, `Sanitaires`, `CVC`;
- les économies de fret et de gestion douanière deviennent significatives;
- certains lots deviennent importables uniquement grâce à la mutualisation.

### 2.8 Optimisation supply chain globale

La vraie optimisation ne doit pas être un simple match `import vs local` :

- intégrer `cashflow` (avantage du paiement à l’import vs délai local);
- intégrer `lead_time` et `risque` dans la décision;
- permettre des scénarios selon la criticité chantier.

## 3. Nouveaux KPI stratégiques

### 3.1 KPI financiers

- `CAPEX_BRUT` = somme des `CAPEX_LOCAL` avant toute décision.
- `CAPEX_IMPORT_SIMPLE` = somme des `CAPEX_IMPORT` calculés en mode import direct (FOB+landed cost sans scénario).
- `CAPEX_IMPORT_OPTIMISE` = somme des importations retenues avec optimisation conteneur / frais réels.
- `CAPEX_DECISION` = somme finale retenue par le moteur de décision (import/local/mixte) pour chaque ligne.
- `POTENTIEL_THEORIQUE_MAX` = somme des gains si toutes les lignes identifiées comme importables étaient importées.
- `ECONOMIE_CAPTUREE` = `CAPEX_BRUT - CAPEX_DECISION`.
- `POTENTIEL_CACHE` = `POTENTIEL_THEORIQUE_MAX - ECONOMIE_CAPTUREE`.

### 3.2 KPI sourcing et risque

- `TAUX_COUVERTURE_SOURCING` = `capex_importable / CAPEX_BRUT` ou `nombre_lignes_importables / lignes_totales`.
- `TAUX_IMPORTABILITE` = `capex_potentiellement_importable / CAPEX_BRUT`.
- `SCORE_PROCUREMENT` = score composite pondéré (`pricing`, `risk`, `lead_time`, `supplier_maturity`, `logistics`).
- `RISQUE_LOGISTIQUE` = score global combinant container, lead time, doublage portuaire et stockage.
- `DEPENDANCE_IMPORT` = `CAPEX_IMPORT / CAPEX_BRUT`.

### 3.3 KPI lot

- `LOT_CAPEX_POTENTIEL` = économie théorique ligne/lot.
- `LOT_IMPORTABILITE` = score de faisabilité import.
- `LOT_RISQUE` = combinaison du risque fournisseur + risque logistique + risque criticité.
- `CONTINUITE_CONTAINER` = lot éligible à FCL / LCL.

## 4. Scénarios avancés

### 4.1 CONSERVATEUR

Règles :

- import si `ECONOMIE > 12 %`
- `RISK_SCORE > 70`
- `LEAD_TIME <= 60 jours`
- `CONTAINER_FILL_RATE >= 0.7`

Résultats :

- `CAPEX` conservateur
- économie faible mais projet sécurisée
- dépendance import maîtrisée
- risque faible

### 4.2 EQUILIBRE

Règles :

- import si `ECONOMIE > 8 %`
- `RISK_SCORE > 55`
- `LEAD_TIME <= 75 jours`
- utilisation FCL/LCL optimisée

Résultats :

- `CAPEX` équilibré
- économie significative
- dépendance import mesurée
- risque géré

### 4.3 AGRESSIF

Règles :

- import si `ECONOMIE > 3 %`
- `RISK_SCORE > 40`
- tous les lots importables candidats peuvent être examinés
- containerisation maximisée

Résultats :

- `CAPEX` maximalement optimisé
- fort potentiel d’économies cachées
- dépendance import élevée
- risque et gestion logistique accrus

### 4.4 Calculs par scénario

Chaque scénario doit recalculer :

- `CAPEX_DECISION`
- `ECONOMIE_CAPTUREE`
- `ROI` = `ECONOMIE_CAPTUREE / CAPEX_BRUT`
- `CONTAINERS_REQUIRED`
- `CASHFLOW_IMPACT`
- `DELAI_MEAN`
- `RISQUE_LOGISTIQUE`
- `DEPENDANCE_IMPORT`

## 5. Analyse par lot

### 5.1 lots optimisables

Identifier automatiquement les lots présentant :

- plus grand delta `CAPEX_LOCAL - CAPEX_IMPORT_SIMPLE`
- `IMPORTABILITY_SCORE` élevé
- `CONTAINER_FILL_RATE` favorable

### 5.2 lots anti-performance

Lister les lots dont :

- `CAPEX_IMPORT` > `CAPEX_LOCAL`
- `RISQUE_LOGISTIQUE` élevé
- `LEAD_TIME` long
- `MOQ` non respectée

### 5.3 lots fortement importables

Identifier ceux avec :

- `SCORE_PROCUREMENT` élevé
- `FILL_RATE` FCL
- `RISK_SCORE` faible
- `POTENTIEL_CACHE` bas

### 5.4 lots non pertinents à importer

- produits volumineux ou lourds non rentables
- piece unique à valeur ajoutée locale
- lots dont `RISQUE_LOGISTIQUE` ou `DELIVERY_RISK` est critique

### 5.5 économies cachées par lot

- présentées comme `POTENTIEL_CACHE`
- capitalisables en mode `AGRESSIF`
- mesurées dans un tableau ordonné `LOT -> ARTICLE`

### 5.6 poids CAPEX par lot

- `LOT_CAPEX_BRUT`
- `LOT_ECONOMIE_POTENTIELLE`
- `LOT_ECONOMIE_CAPTURÉE`

## 6. Optimisation du moteur

### 6.1 architecture calcul scalable

Proposer :

- `core/calculator.py` reste baseline V1
- `core/procurement_engine.py` enrichit chaque ligne
- `core/decision_engine.py` calcule la décision multi-critère
- `core/logistics_engine.py` calcule containers/fret/delivery
- `core/scenario_engine.py` génère trois scénarios
- `core/analytics_engine.py` agrège KPI STAR schema

### 6.2 optimisation PostgreSQL

- conserver schéma DIM → FACT existant
- ajouter `dim_scenario`, `fact_line_simulation`, `fact_procurement_analysis`
- calculer les KPI agrégés côté SQL pour Power BI
- exposer une vue `vw_capex_scenarios`

### 6.3 optimisation FastAPI

- préserver toutes les routes existantes
- ajouter des champs enrichis sans modifier les payloads existants obligatoires
- créer de nouvelles routes `GET /analytics/procurement`, `GET /analytics/scenarios`, `GET /analytics/lot-analysis`
- garder `ServiceSimulation` comme façade publique

### 6.4 optimisation Power BI

- modèles basés sur `fact_simulation` + `dim_scenario` + `dim_lot` + `dim_fournisseur`
- cross-filtering sur catégories, lots, scénarios, risques
- drill-down `LOT -> ARTICLE`
- drill-through `FOURNISSEUR`

### 6.5 optimisation cross-filtering

- calculer et exposer les dimensions clés : `scenario`, `lot`, `famille`, `supplier_maturity`, `risk_band`
- utiliser des mesures DAX simples sur des faits compatibles Power BI

### 6.6 optimisation AG Grid

- conserver structure de colonnes actuelles
- enrichir avec colonnes additionnelles en `field` non obligatoires
- utiliser des `rowGroup` pour `lot`, `famille`, `decision`
- filtrage sur `SCORE_PROCUREMENT`, `RISQUE_LOGISTIQUE`, `POTENTIEL_CACHE`

### 6.7 réduction consommation tokens IA

- limiter l’utilisation IA à l’enrichissement de données qualité et à l’auto-classification des familles
- conserver les calculs financiers dans Python / SQL
- stocker les résultats d’analyse IA en cache et en DB

### 6.8 calculs auditables et traçables

- ajouter un identifiant de ligne `simulation_line_id`
- conserver `DECISION_REASON` et `PROCUREMENT_ANALYSIS`
- historiser les paramètres utilisés (`seuil_decision_import`, `taux_landed_cost`, `scenario`)
- exposer un `audit_trail` dans la réponse API

## 7. Power BI / Frontend recommandé

### 7.1 Storytelling exécutif

Dashboard direction avec :

- `CAPEX_BRUT`
- `ECONOMIE_CAPTUREE`
- `POTENTIEL_CACHE`
- `TAUX_IMPORTABILITE`
- `RISQUE_LOGISTIQUE`
- `DEPENDANCE_IMPORT`
- comparaison `CONSERVATEUR / EQUILIBRE / AGRESSIF`

### 7.2 Dashboard procurement

- `SCORE_PROCUREMENT` par lot
- `TAUX_COUVERTURE_SOURCING`
- `IMPORT_CONFIDENCE`
- `SUPPLIER_MATURITY`
- `CASHFLOW_IMPACT`

### 7.3 Dashboard audit import

- `IMPORTABILITY_SCORE` par article
- `hidden savings` / `POTENTIEL_CACHE`
- `risks` vs `savings`
- `cost breakdown` Chine → Pointe-Noire

### 7.4 Dashboard supply chain

- `container fill rate`
- `logistics cost` vs `capex savings`
- `lead time distribution`
- `warehouse / delivery risk`

### 7.5 Dashboard scénarios

- barre comparative par scénario
- `CAPEX_DECISION` vs `CAPEX_IMPORT_SIMPLE`
- `cashflow` et `délai`
- `risk bands`
- `dependance import`

### 7.6 cross-filtering type Power BI

- possibilité de filtrer sur :
  - scénario
  - lot
  - famille
  - fournisseur
  - score procurement
  - niveau de risque

### 7.7 drill-down et drill-through

- drill-down `LOT → ARTICLE`
- drill-through `FOURNISSEUR` via `supplier_id`
- heatmaps économies par lot/famille
- matrices risques par port / fournisseur
- waterfall CAPEX montrant `CAPEX_LOCAL → CAPEX_DECISION`

## 8. Livrables recommandés

- audit complet du moteur actuel ✅
- problèmes détectés ✅
- architecture cible ✅
- stratégie de migration sans casse ✅
- nouvelles mesures/KPI ✅
- pseudo-code calculs ✅
- structure backend recommandée ✅
- structure frontend recommandée ✅
- structure Power BI recommandée ✅
- stratégie enterprise procurement ✅

## 9. Contraintes importantes

- ne pas réécrire le moteur existant
- ne pas modifier les routes/API existantes
- ne pas toucher aux modules hors périmètre
- conserver la structure DIM → FACT actuelle
- conserver la logique AG Grid actuelle
- conserver le dark theme premium
- conserver les calculs auditables

## 10. Conclusions clés

1. Le principal frein est le modèle de coût import trop conservateur : ratio FOB global + landed cost fixe 52 %.
2. Le deuxième frein est l’absence de consolidation multi-lots / optimisation containers.
3. Le troisième frein est l’absence d’une vraie logique `decision_engine` multi-critère qui pondère le risque, le délai et la criticité.
4. L’existant peut être conservé comme baseline V1 si l’on ajoute une couche `ProcurementEngine` / `DecisionEngine` / `LogisticsEngine` autour.
5. Pour Pointe-Noire, il faut calibrer la logique sur des fournisseurs Chine concrets et séparer nettement : `CAPEX_IMPORT_SIMPLE`, `CAPEX_IMPORT_OPTIMISE`, `CAPEX_DECISION`.

## 11. Pseudo-code recommandé

```python
class CAPEXOptimizer:
    def __init__(self, params):
        self.calculator = CalculateurCAPEX(params)
        self.procurement = ProcurementEngine()
        self.decision = DecisionEngine(params)
        self.logistics = LogisticsEngine()
        self.scenario = ScenarioEngine(params)

    def enrich_line(self, line):
        base = self.calculator.optimiser_ligne(line)
        procurement = self.procurement.enrich_line(line)
        logistic = self.logistics.enrich_line({**line, **base})
        decision = self.decision.enrich_line({**base, **procurement, **logistic})
        return {
            **line,
            **base,
            **procurement,
            **logistic,
            **decision,
            "POTENTIEL_THERORIQUE_MAX": self._compute_max_potential(line),
        }

    def compute_scenario(self, lines, scenario):
        for line in lines:
            enriched = self.enrich_line(line)
            enriched["CAPEX_DECISION"] = self._scenario_decision(enriched, scenario)
            enriched["CONTAINERS_REQUIRED"] = self.logistics.container_engine.containers_required(enriched)
        return self._aggregate(lines)
```

## 12. Recommandation immédiate

- ajouter un audit coeur moteur sans casser les routes;
- créer un `ServiceSimulation` enrichi qui calme la conservativité du calcul import en mode `EQUILIBRE` et `AGRESSIF`;
- exposer de nouveaux KPI sans changer les clés obligatoires existantes;
- garder la route `/simulation/simulate` compatible et utiliser les nouveaux champs uniquement comme enrichissement.
