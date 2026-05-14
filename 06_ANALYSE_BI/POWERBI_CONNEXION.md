# Connexion Power BI - SP2I CAPEX

Le fichier `modele_powerbi.pbix` actuel n'est pas un vrai rapport Power BI.
Il s'agit d'un placeholder texte, donc Power BI Desktop l'affiche comme
endommagé.

## Créer un nouveau rapport Power BI

1. Ouvrir Power BI Desktop.
2. Cliquer sur `Obtenir les donnees`.
3. Choisir `Base de donnees PostgreSQL`.
4. Renseigner :

```text
Serveur : localhost
Base    : sp2i_capex
```

5. Choisir le mode :

```text
DirectQuery
```

6. Utiliser les identifiants :

```text
Utilisateur : user
Mot de passe : password
```

7. Charger les tables :

```text
fact_metre
dim_famille
```

## Relation du modèle

Créer la relation suivante :

```text
dim_famille[famille] 1 -> * fact_metre[famille]
```

## Mesures DAX recommandées

```DAX
CAPEX_LOCAL = SUM(fact_metre[prix_total_ht])
```

```DAX
CAPEX_OPTIMISE = SUM(fact_metre[capex_optimise])
```

```DAX
ECONOMIE = SUM(fact_metre[economie_nette])
```

```DAX
TAUX_ECO = DIVIDE([ECONOMIE], [CAPEX_LOCAL], 0)
```

## Vérification rapide

Depuis PowerShell :

```powershell
$env:PGPASSWORD="password"
psql -h localhost -U user -d sp2i_capex -c "SELECT COUNT(*) FROM fact_metre;"
psql -h localhost -U user -d sp2i_capex -c "SELECT COUNT(*) FROM dim_famille;"
```

Valeurs attendues :

```text
fact_metre  : 178 lignes
dim_famille : 5 lignes
```
