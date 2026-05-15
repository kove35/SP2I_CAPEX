# Modele de risque import

Le risque import est decoupe en quatre familles.

```text
fournisseur
pays
logistique
chantier
```

## Fournisseur

Le moteur regarde la fiabilite, la qualite et les retards.

Un fournisseur avec faible fiabilite ou fort taux de defaut augmente le risque
d'import, meme si le prix est attractif.

## Pays

Le modele prepare les risques :

```text
douane
port
logistique
change
politique
```

Pour Chine -> Pointe-Noire, les risques de douane, port et delai sont
importants car ils peuvent bloquer le planning chantier.

## Logistique

Le risque logistique tient compte de la congestion portuaire, du transport
maritime et du transport local Congo.

## Chantier

Une ligne critique pour le planning supporte moins bien un retard. Le meme
produit peut donc etre acceptable sur un lot non critique, mais dangereux sur
un lot bloquant.
