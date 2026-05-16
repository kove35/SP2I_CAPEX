# Pipeline de test cloud SP2I

## Flux complet

```text
Upload fichier
    |
    v
FastAPI /api/upload/excel
    |
    v
Analyse IA hybride
    |
    v
Validation humaine
    |
    v
FastAPI /api/upload/excel/sync
    |
    v
PostgreSQL fact_metre + dimensions
    |
    v
Power BI Service
```

## Scenarios de test

### Scenario 1 : Excel propre

Objectif : verifier que le fichier passe sans correction humaine lourde.

Controle attendu :

- lots detectes
- colonnes quantite/prix/designation reconnues
- KPI non nuls
- lignes inserees dans PostgreSQL

### Scenario 2 : CSV export ERP

Objectif : verifier le support cloud des exports simples.

Controle attendu :

- separateur detecte
- preview tabulaire visible
- erreurs comprehensibles si mapping insuffisant

### Scenario 3 : ancien Excel XLS

Objectif : verifier la compatibilite avec les fichiers historiques.

Controle attendu :

- lecture via `xlrd`
- feuilles converties en lignes tabulaires
- message clair si le fichier est corrompu

### Scenario 4 : PDF DQE

Objectif : valider l'extraction texte.

Controle attendu :

- endpoint `/dqe/extract` repond
- preview texte disponible
- pas d'ecriture automatique en base

### Scenario 5 : fichier trop lourd

Objectif : verifier la securite upload.

Controle attendu :

- HTTP 413
- message lisible
- backend stable

## Validation KPI

Apres synchronisation :

```text
GET /capex/summary
GET /fact_metre?limit=50
```

Dans PostgreSQL :

```sql
SELECT COUNT(*) FROM fact_metre;
SELECT SUM(capex_local), SUM(capex_optimise), SUM(economie) FROM fact_metre;
SELECT lot, COUNT(*) FROM fact_metre GROUP BY lot ORDER BY lot;
```

## Erreurs a surveiller

- Lots manquants apres parsing.
- `capex_local` egal a zero alors que le DQE contient des montants.
- Moyenne de taux utilisee dans Power BI au lieu du ratio des totaux.
- Colonnes Power BI connectees a des textes au lieu des IDs.

## Definition d'un test reussi

Un test cloud est reussi lorsque :

- Streamlit atteint FastAPI.
- FastAPI atteint PostgreSQL.
- L'upload produit une preview IA.
- La synchronisation alimente `fact_metre`.
- Les KPI API correspondent aux sommes SQL.
- Power BI affiche les donnees apres rafraichissement.
