# Strategie Mapping IA Excel

## Objectif

Mapper des colonnes heterogenes vers les champs standards SP2I.

Exemples :

```text
QTE, Qté, Qt, Q, Nbr -> quantite
PU, P.U, Prix Unit. -> prix_unitaire_ht
Montant, Prix HT -> prix_total_ht
```

## Methode actuelle

Le mapping utilise :

- normalisation des libelles
- synonymes metier
- inclusion/prefixe/suffixe
- fuzzy matching
- score de confiance
- raison auditable

Exemple :

```json
{
  "source_column": "Qt",
  "mapped_to": "quantite",
  "confidence": 0.93,
  "reason": "Colonne rapprochee de 'qte' par fuzzy matching."
}
```

## Validation humaine

Les colonnes a faible confiance sont marquees comme ambigues. L'utilisateur doit
valider ou corriger avant synchronisation PostgreSQL.

Endpoint :

```http
POST /dqe/validate-mapping/{file_id}
```

## Evolution future

Les embeddings pourront enrichir le mapping en comparant les colonnes avec :

- anciens DQE
- mappings valides
- familles metier
- vocabulaires fournisseurs

