# Logique de scoring decisionnel

Le score final est volontairement simple pour rester explicable.

## Criteres

```text
economie
risque
delai
criticite chantier
```

Les poids sont centralises dans :

```text
07_API_BACKEND/app/core/decision_parameters.py
```

Valeurs par defaut :

```text
WEIGHT_SAVINGS     = 0.40
WEIGHT_RISK        = 0.25
WEIGHT_LEAD_TIME   = 0.20
WEIGHT_CRITICALITY = 0.15
```

## Formule

```text
score_final =
    score_economie   * poids_economie
  + score_risque     * poids_risque
  + score_delai      * poids_delai
  + score_criticite  * poids_criticite
```

Chaque sous-score est conserve dans `DECISION_REASON`. Cela permet d'expliquer
pourquoi une ligne est recommandee en `IMPORT`, `LOCAL` ou `MIXTE`.

## Seuils

```text
score >= 65  -> IMPORT
score >= 45  -> MIXTE
score < 45   -> LOCAL
```

Ces seuils sont parametrables. Ils ne doivent pas etre dupliques dans Power BI.

## Confiance

La confiance qualifie la robustesse du score :

```text
HIGH   : score >= 75
MEDIUM : score >= 50
LOW    : score < 50
```

La confiance n'est pas une verite absolue. Elle sert a guider les revues
metier : une decision `LOW` doit etre relue avant validation.
