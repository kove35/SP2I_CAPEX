# Risk Engine

Le risque est une composante du Decision Engine. Il mesure si l'import reste
acceptable malgre le gain financier.

## Sources de risque

Le modele prepare plusieurs axes :

```text
fournisseur
logistique
pays
douane
geopolitique
devise
```

Les dimensions PostgreSQL ajoutees sont :

```text
dim_supplier
dim_country
dim_risk_level
```

## Score fournisseur

`dim_supplier` porte les informations stables :

```text
risk_score
quality_score
lead_time_avg
delivery_score
financial_score
```

Au depart, les simulations sans fournisseur utilisent `NON_RENSEIGNE`. Cela
conserve les relations Power BI sans inventer une donnee metier.

## Score pays

`dim_country` prepare les risques :

```text
customs_risk
logistics_risk
geopolitical_risk
currency_risk
```

Ces champs permettront plus tard d'enrichir les scenarios d'import Chine,
Europe, local ou multi-sourcing.

## Vue Power BI

La vue principale est :

```text
v_decision_risk
```

Elle agrège les lignes par scenario, decision, type de decision et niveau de
risque. Power BI doit l'utiliser pour visualiser les risques, pas pour les
recalculer.
