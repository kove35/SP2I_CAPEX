# SP2I CAPEX — Protection des données

## Règle de publication

Le dépôt ne doit contenir que des données de démonstration anonymisées et
explicitement autorisées à la publication.

Sont considérés privés par défaut :

- DQE clients et métrés réels ;
- noms, coordonnées et conditions de fournisseurs ;
- prix négociés, prix FOB et marges ;
- chaînes de connexion, clés API et identifiants ;
- exports Power BI contenant des données de production ;
- journaux d'audit associés à un projet réel.

## Emplacements locaux ignorés

Utiliser `private_data/` ou les sous-dossiers `private/` prévus dans les zones
d'entrée, de référence et de résultat. Ces chemins sont exclus de Git.

## Contrôle avant publication

1. Vérifier le propriétaire et l'autorisation de publication.
2. Remplacer noms, emails, téléphones et identifiants de projet.
3. Neutraliser les prix et références fournisseur si le fichier sert de démo.
4. Vérifier les métadonnées des fichiers Office et PDF.
5. Examiner `git diff --cached --name-only` avant chaque commit.

## Fichiers historiques déjà suivis

Les fichiers Excel/CSV/PDF actuellement suivis doivent être classés par le
propriétaire en trois groupes : `PUBLIC_DEMO`, `INTERNE` ou `CONFIDENTIEL`.
Les fichiers `INTERNE` et `CONFIDENTIEL` devront ensuite être retirés de Git et,
si nécessaire, purgés de l'historique avec rotation des secrets exposés.

Cette opération n'est pas automatisée, car supprimer ou réécrire l'historique
sans validation de propriété pourrait entraîner une perte de données.
