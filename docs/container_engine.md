# Container Engine

Le `ContainerEngine` calcule le plan container d'une ligne import.

## Capacites utilisees

```text
20FT : 33 m3 utiles
40FT : 67 m3 utiles
40HC : 76 m3 utiles
```

Le moteur calcule :

```text
volume total
poids total
type container
nombre de containers
taux de remplissage
cout container ou cout LCL
```

## FCL vs LCL

`FCL` signifie container complet. `LCL` signifie groupage : la marchandise
partage le container avec d'autres marchandises.

Le moteur conseille `LCL` quand le remplissage est faible, car envoyer un
container presque vide cree un faux cout logistique.
