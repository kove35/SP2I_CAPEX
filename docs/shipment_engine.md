# Shipment Engine

Le `ShipmentEngine` suit le flux logistique jusqu'au chantier.

## Statuts

```text
READY
IN_PRODUCTION
AT_PORT
ON_VESSEL
AT_SEA
AT_CUSTOMS
DELIVERED
ON_SITE
```

Chaque statut permet d'estimer le nombre de jours restants et le risque de
retard chantier.

## Flux cible

```text
Usine Chine
  -> Consolidation
  -> Port Chine
  -> Transport maritime
  -> Port Pointe-Noire
  -> Douane
  -> Transport local
  -> Chantier
```

L'ETA chantier est historisee pour que Power BI puisse suivre les risques de
planning.
