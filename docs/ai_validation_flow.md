# Flux Validation IA Excel

## Objectif

Conserver l'humain comme decisionnaire final.

## Parcours

```text
1. Upload Excel
2. Analyse IA hybride
3. Preview intelligente
4. Suggestions mapping
5. Controle anomalies
6. Validation humaine
7. Synchronisation PostgreSQL
8. Simulation CAPEX
```

## Pourquoi cette validation est importante

Les fichiers DQE reels peuvent contenir :

- cellules fusionnees
- sous-totaux
- lots implicites
- colonnes ambiguës
- lignes commentaires
- structures verticales

L'IA peut proposer, mais l'utilisateur confirme.

## UX recommandee

Dans `/app/dqe` :

- afficher le score global
- afficher les colonnes reconnues
- afficher les colonnes ambigues
- afficher les anomalies
- proposer un bouton `Valider mapping IA`
- interdire la synchronisation sans controle visuel

