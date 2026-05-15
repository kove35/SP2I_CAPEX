# Modele de delai import

Le `LeadTimeEngine` calcule le delai complet d'import.

Hypothese par defaut Chine -> Pointe-Noire :

```text
production fournisseur : 15 jours
transport maritime     : 45 jours
douane Congo           : 7 jours
transport local        : 3 jours
marge securite         : 10 jours
```

Total par defaut :

```text
80 jours
```

Ce delai est historise dans `fact_simulation.lead_time_days`. Power BI peut le
visualiser par scenario, famille, lot ou fournisseur.

## Pourquoi le delai compte

Un import peut etre moins cher mais incompatible avec le planning chantier. Le
delai devient donc un critere d'arbitrage, pas seulement une information.
