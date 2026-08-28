# SP2I CAPEX — Organisation du projet Work

## Nom recommandé

**SP2I CAPEX — Pilotage & Développement**

Le projet Work rassemble les chats, fichiers de référence et décisions qui
doivent rester disponibles pendant toute la durée du produit.

## Objectif commun

Construire un cockpit fiable d'analyse DQE et de pilotage CAPEX, avec :

- import et contrôle qualité des DQE ;
- comparaison local/import ;
- cockpit opérationnel React ;
- analytics stratégique Power BI ;
- API FastAPI et source de vérité PostgreSQL ;
- traçabilité, gouvernance et sécurité SaaS.

## Instructions de projet à placer dans Work

```text
Tu travailles sur SP2I CAPEX, plateforme de pilotage des investissements
immobiliers et d'analyse DQE.

Priorités : sécurité, qualité des données, cohérence financière, filtres,
performance, puis nouvelles fonctionnalités.

React est le cockpit opérationnel. Power BI reste la couche stratégique.
FastAPI porte la logique métier. PostgreSQL est la source de vérité.

Avant toute modification, inspecte la version actuelle du dépôt. Préserve les
travaux existants. Ne pousse jamais un secret ou un DQE confidentiel.

Pour chaque changement, indique : objectif, fichiers concernés, validations,
risques, résultat et prochaine étape. Ne considère jamais une modification
comme terminée si le build ou les tests concernés n'ont pas été exécutés.
```

## Chats à créer

Utiliser un chat distinct pour chaque résultat attendu :

1. `00 — Pilotage et feuille de route`
2. `01 — Sécurité et authentification`
3. `02 — Pipeline DQE et qualité des données`
4. `03 — Backend FastAPI et PostgreSQL`
5. `04 — Frontend React et UX responsive`
6. `05 — Power BI, modèle et filtres`
7. `06 — Calculs CAPEX et Cost Intelligence`
8. `07 — Tests, CI/CD et déploiement`
9. `08 — Documentation et décisions techniques`

Archiver un chat lorsqu'un résultat est livré. Continuer un chat uniquement si
la nouvelle demande concerne exactement le même résultat.

## Sources durables à joindre au projet

- dépôt GitHub `kove35/SP2I_CAPEX` ;
- cahier des charges fonctionnel validé ;
- dictionnaire de données et hiérarchie BIM ;
- modèle Power BI de référence ;
- DQE de démonstration anonymisé ;
- décisions d'architecture ;
- rapports d'audit et plans de correction.

Ne pas placer dans les sources partagées des mots de passe, chaînes de
connexion, clés API ou fichiers fournisseurs confidentiels.

## Rythme de pilotage

Chaque lot de travail suit ce cycle :

1. cadrage du résultat attendu ;
2. diagnostic fondé sur le code ou les données actuels ;
3. modification limitée au périmètre ;
4. tests et réconciliation ;
5. synthèse de livraison ;
6. mise à jour de la feuille de route.

