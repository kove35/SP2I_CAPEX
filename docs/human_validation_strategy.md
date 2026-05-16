# Strategie Human-in-the-loop SP2I

## Principe

SP2I doit etre intelligent sans devenir opaque. Chaque proposition IA doit etre
visible, explicable et validable.

## Responsabilites

IA :

- propose
- explique
- score
- detecte
- signale

Humain :

- valide
- corrige
- confirme
- autorise la synchronisation

Backend :

- normalise
- simule
- historise
- synchronise PostgreSQL

Power BI :

- visualise uniquement les donnees deja controlees

## Regle de securite

L'IA ne doit jamais ecrire directement dans PostgreSQL. Elle prepare une analyse
et un mapping. Le pipeline controle realise ensuite l'ecriture.

