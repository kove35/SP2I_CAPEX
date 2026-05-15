# Flux simulation

## Endpoint principal

```text
POST /simulation/simulate
```

Payload simplifie :

```json
{
  "items": [
    {
      "designation": "Cable electrique",
      "quantite": 10,
      "prix_total_ht": 1000,
      "lot": "Lot 4"
    }
  ],
  "mode": "strict",
  "summary_only": false,
  "return_lines": true,
  "persist": false
}
```

## Mode strict

Utilise pour :

- frontend ;
- simulation officielle ;
- saisie utilisateur.

Comportement :

- refuse les lignes invalides ;
- retourne une erreur structuree ;
- evite de masquer une mauvaise donnee.

## Mode tolerant

Utilise pour :

- import Excel massif ;
- pipeline DQE ;
- donnees partielles.

Comportement :

- conserve les lignes ;
- ajoute des warnings ;
- tague les anomalies ;
- evite de perdre silencieusement les donnees.

## Identifiants techniques

Chaque simulation retourne :

```text
simulation_id
run_id
scenario_id
```

Aujourd'hui, ces IDs sont generes en memoire. Demain, ils seront sauvegardes en
base pour historiser les scenarios.

## Options API

`summary_only`

- `true` : retourne uniquement KPI et metadata ;
- utile pour les gros volumes.

`return_lines`

- `true` : retourne les lignes detaillees ;
- `false` : evite les gros payloads.

`persist`

- reserve pour la future historisation ;
- aujourd'hui retourne seulement l'intention dans les metadata.

## PostgreSQL vs Power BI

Python calcule les lignes.

PostgreSQL calcule les KPI globaux et expose les vues analytiques.

Power BI affiche, filtre et fait le drill-down.

Power BI ne doit pas recalculer :

- CAPEX ;
- economie ;
- decision import/local ;
- mapping famille ;
- nettoyage DQE.
