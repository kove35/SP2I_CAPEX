# Site Logistics

Le `SiteLogisticsEngine` analyse l'arrivee chantier.

## Deux risques opposes

```text
arrivee trop tot  -> stockage couteux ou site sature
arrivee trop tard -> chantier bloque
```

## Indicateurs

```text
storage_cost
site_saturation_rate
delivery_risk
delivery_priority
```

Ces indicateurs alimentent Power BI via :

```text
v_delivery_risk
v_logistics_costs
```

L'objectif est de rapprocher la decision achat du planning chantier reel.
