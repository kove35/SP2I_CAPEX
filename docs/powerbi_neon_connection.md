# Power BI - Connexion a Neon PostgreSQL

## Parametres

Utiliser les informations fournies par Neon pour le projet `SP2I_CAPEX`.

```text
Serveur : HOST.neon.tech
Base    : neondb
Utilisateur : USER
Mot de passe : PASSWORD
SSL     : requis
Mode    : Import recommande
```

## Source Power BI

Dans Power BI Desktop :

1. Choisir `Obtenir les donnees`.
2. Choisir `Base de donnees PostgreSQL`.
3. Serveur : `HOST.neon.tech`.
4. Base de donnees : `neondb`.
5. Mode de connectivite : `Importer`.
6. Renseigner utilisateur et mot de passe Neon.
7. Activer SSL si l'assistant le demande.

## Tables a charger

Charger uniquement ces vues :

- `vw_capex_summary`
- `vw_project_kpis`
- `vw_dashboard_direction`
- `vw_dashboard_import`
- `vw_dashboard_chantier`

Ne pas connecter Power BI directement a `fact_metre` pour les dashboards standards.

## Controle attendu

```sql
SELECT COUNT(*) FROM fact_metre;
-- 290

SELECT SUM(capex_local) FROM fact_metre;
-- 113928000

SELECT * FROM vw_capex_summary;
-- nb_lignes = 290, capex_brut ~= 113928000
```

