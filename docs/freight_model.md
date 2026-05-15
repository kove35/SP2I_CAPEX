# Modele de cout fret

Le `FreightEngine` estime le cout logistique complet.

## Composantes

```text
freight_cost
port_cost
customs_cost
insurance_cost
local_delivery_cost
storage_cost
```

## Formule

```text
total_logistics_cost =
  fret maritime
  + cout port
  + douane
  + assurance
  + livraison locale
  + stockage
```

Ces valeurs sont historisees dans `fact_simulation` via `shipment_cost` et
`storage_cost`. Power BI affiche les couts, mais ne les recalcule pas.
