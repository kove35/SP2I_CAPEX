# Inventaire des données suivies par Git

Audit réalisé le 29 août 2026 sur les fichiers `.xlsx`, `.xls`, `.csv` et `.pdf`
suivis par Git.

## Résultat

| Périmètre | Fichiers | Classification | Action avant publication |
|---|---:|---|---|
| `03_DONNEES_ENTREE/` | 2 | Restreint — DQE/source métier | Retirer du dépôt public ou confirmer qu'ils sont synthétiques |
| `03_DONNEES_REFERENCE/` | 6 | Restreint — masters et archives DQE | Retirer du dépôt public ou confirmer qu'ils sont synthétiques |
| `02_REFERENTIELS/` | 2 | Interne — ratios/mappings | Valider la licence et la confidentialité |
| `05_RESULTATS/` | 3 | Interne — résultats dérivés | Ne pas publier si produits depuis un DQE client |
| `06_ANALYSE_BI/` | 2 | Interne — datasets dérivés | Les deux CSV présents sont vides |
| Racine | 64 | À qualifier — tests, benchmarks, fournisseurs et gouvernance | Conserver uniquement les jeux synthétiques documentés |

Total : **79 fichiers**, **2 623 566 octets**. Quatre CSV sont vides. Une
inspection textuelle des classeurs a détecté des termes métier (prix, CAPEX,
client ou fournisseur) dans **55 classeurs**. Aucun terme évident de secret
technique ni adresse e-mail n'a été détecté dans les chaînes partagées ; cela
ne prouve pas l'absence de données confidentielles dans les cellules, formules,
commentaires ou objets intégrés.

## Décision de sécurité

Le dépôt ne doit pas être rendu ou maintenu public tant que les huit fichiers
DQE/source des dossiers `03_DONNEES_ENTREE` et `03_DONNEES_REFERENCE` n'ont pas
été qualifiés par le propriétaire des données. Une suppression dans un futur
commit ne retire pas leur contenu de l'historique Git existant.
