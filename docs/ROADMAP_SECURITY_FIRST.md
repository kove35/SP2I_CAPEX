# SP2I CAPEX — Roadmap sécurité d'abord

## Phase 0 — Blocage des risques critiques

- Forcer l'inscription publique au rôle `VIEWER`.
- Rendre `SP2I_JWT_SECRET` obligatoire en production.
- Protéger les endpoints métier, uploads, exports et diagnostics.
- Ajouter une autorisation par utilisateur, rôle et projet.
- Désactiver les routes debug en production.
- Auditer les fichiers métier suivis dans le dépôt public.

**Sortie attendue :** aucun utilisateur anonyme ne peut lire les données métier,
modifier le DQE, exporter des données ou obtenir des diagnostics internes.

## Phase 1 — Pipeline DQE fiable

- Sécuriser les uploads avant chargement complet en mémoire.
- Valider le type réel et la structure des fichiers.
- Rendre la synchronisation transactionnelle et restaurable.
- Séparer clairement données métier propres et audit technique.
- Ajouter les contrôles de complétude, unicité et réconciliation.

**Sortie attendue :** une importation erronée ne peut ni corrompre ni remplacer
silencieusement la source de vérité.

## Phase 2 — Qualité logicielle

- Ajouter les dépendances de test backend.
- Ajouter lint et tests unitaires frontend.
- Créer une CI pour compilation, tests et build.
- Faire du healthcheck un vrai contrôle de disponibilité.
- Remplacer les créations/migrations automatiques au démarrage par des
  migrations versionnées.

## Phase 3 — Maintenabilité et performance

- Découper les services et pages surdimensionnés.
- Unifier les implémentations concurrentes du workflow.
- Réduire le bundle frontend initial par chargement différé.
- Retirer la journalisation PostgreSQL synchrone de chaque requête.

## Phase 4 — Reprise fonctionnelle

- Stabiliser les filtres BIM et Power BI.
- Revalider les calculs local/import et Cost Intelligence.
- Reprendre procurement, logistique, chantier et fonctionnalités IA.

