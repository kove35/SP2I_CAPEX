# SP2I CAPEX — Déploiement sécurisé

## Variables Render obligatoires

```text
ENVIRONMENT=production
SP2I_JWT_SECRET=<secret aléatoire d'au moins 32 caractères>
FRONTEND_URL=https://sp-2-i-capex.vercel.app
CORS_ORIGINS=https://sp-2-i-capex.vercel.app
CORS_ORIGIN_REGEX=
ALLOW_STARTUP_SCHEMA_MUTATIONS=false
ENABLE_DB_REQUEST_METRICS=false
```

Générer le secret hors du dépôt et le stocker uniquement dans le gestionnaire
de variables Render. Ne jamais le copier dans `.env.example`, GitHub ou un
document partagé.

## Avant le premier redéploiement

1. Vérifier que les tables ORM déjà utilisées existent dans PostgreSQL.
2. Sauvegarder la base Neon/PostgreSQL.
3. Appliquer les migrations SQL manquantes hors du démarrage de l'API.
4. Configurer les variables ci-dessus.
5. Redéployer le backend.
6. Vérifier `/health/live`, puis `/health`.
7. Vérifier que `/docs` et `/openapi.json` sont indisponibles en production.
8. Vérifier qu'une requête anonyme vers `/analytics/kpis` retourne `401`.

## Administrateur initial

Exécuter la commande dans un environnement disposant de `DATABASE_URL` :

```bash
PYTHONPATH=07_API_BACKEND python -m app.scripts.create_admin --email admin@example.com
```

Le mot de passe est demandé de façon interactive et n'apparaît pas dans la
commande. L'administrateur peut ensuite attribuer les rôles via les endpoints
protégés `/auth/users` et `/auth/users/{user_id}/role`.

## Matrice de rôles

| Rôle | Accès principal |
|---|---|
| VIEWER | Compte et projets autorisés |
| ANALYST | Analytics, DQE en prévisualisation, simulations |
| MANAGER | Synchronisation DQE et décisions d'approbation |
| ADMIN | Diagnostic, utilisateurs, rôles et configuration |

## Retour arrière

En cas d'incident, revenir au commit précédent et restaurer la sauvegarde de
base si une migration a été appliquée. Ne pas réactiver un secret JWT faible :
générer un nouveau secret et reconnecter les utilisateurs.
