# SP2I CAPEX — Instructions Codex

## Mission du produit

SP2I CAPEX est une plateforme de pilotage des investissements immobiliers et
d'analyse DQE. Le coeur du produit est la fiabilité des données CAPEX :

`DQE / métrés / BPU -> normalisation -> contrôle qualité -> PostgreSQL -> API -> React / Power BI`

React est le cockpit opérationnel. Power BI reste la couche d'analyse
stratégique. FastAPI porte les règles métier et PostgreSQL est la source de
vérité.

## Priorités obligatoires

1. Sécurité et contrôle d'accès.
2. Fiabilité du pipeline DQE et traçabilité des données.
3. Cohérence des calculs CAPEX local/import et des économies.
4. Stabilité des filtres analytiques.
5. Performance et expérience PC, tablette et mobile.
6. Nouvelles fonctionnalités seulement après les points précédents.

## Règles de travail

- Inspecter le code et les changements existants avant toute modification.
- Ne jamais écraser une modification utilisateur non liée à la tâche.
- Garder l'ingestion, la logique métier, l'accès aux données, l'API et
  l'interface clairement séparés.
- Ne pas calculer dans React un KPI qui appartient au backend ou à PostgreSQL.
- Toute évolution de données doit préserver l'audit : source, ligne source,
  statut, confiance, motif d'exclusion et date de traitement quand applicables.
- Utiliser des requêtes SQL paramétrées. Ne jamais concaténer une valeur
  utilisateur dans du SQL.
- Aucun secret, fichier `.env`, identifiant client ou DQE confidentiel ne doit
  être ajouté au dépôt.
- Ne pas ajouter une dépendance de production sans justification explicite.
- Les endpoints de diagnostic ne doivent pas être publics en production.
- Une route destructive ou modifiant la source DQE exige authentification,
  autorisation par projet et transaction.

## Source de vérité métier

- Le DQE métier propre et l'audit technique sont deux couches distinctes.
- `FACT_METRE` et les vues validées sont les sources analytiques.
- La hiérarchie de filtre cible est :
  `projet -> bâtiment -> niveau -> appartement -> pièce -> lot -> famille -> article`.
- Les relations BI doivent rester à sens unique des dimensions vers les faits,
  sauf justification documentée et testée.
- Toute modification d'un calcul financier doit inclure une réconciliation
  avant/après sur CAPEX brut, CAPEX optimisé, économie et nombre de lignes.

## Validation minimale

Avant de déclarer une tâche terminée :

- Backend : compilation Python et tests concernés.
- Frontend : `npm run build` et tests concernés.
- Données/SQL : exécuter les requêtes de validation et documenter le rollback.
- API : vérifier au minimum le contrat de réponse et les cas d'erreur.
- UI : vérifier l'état chargement, vide, erreur et responsive.

Si une validation ne peut pas être exécutée, l'indiquer clairement avec la
cause et ne pas présenter le point comme validé.

## Code Review Rules

- Bloquer toute auto-attribution du rôle `ADMIN` lors de l'inscription.
- Bloquer tout secret JWT par défaut utilisable en production.
- Signaler toute route métier ou debug sensible sans authentification.
- Signaler tout upload contrôlé seulement après chargement complet en mémoire.
- Signaler toute migration implicite exécutée au démarrage de l'application.
- Signaler les divergences de calcul entre backend, vues SQL, React et Power BI.
- Signaler les fichiers métier potentiellement confidentiels ajoutés au dépôt.

## Documentation de pilotage

- Organisation Work : `docs/WORK_PROJECT.md`
- Méthode Codex : `docs/CODEX_WORKFLOW.md`
- Priorités techniques : `docs/ROADMAP_SECURITY_FIRST.md`

