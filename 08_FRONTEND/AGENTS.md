# Frontend React — Instructions Codex

Ces règles complètent les instructions du `AGENTS.md` racine.

## Responsabilités

- React affiche et orchestre ; les KPI financiers sont calculés côté backend.
- Les filtres globaux utilisent une source d'état unique.
- Les paramètres envoyés à l'API doivent conserver les noms du contrat backend.
- Chaque écran gère explicitement chargement, absence de données et erreur.
- Préserver une navigation sans long scroll et responsive PC/tablette/mobile.

## Sécurité

- Ne jamais choisir ou envoyer un rôle privilégié depuis l'inscription publique.
- Ne pas considérer une session de démonstration comme une authentification.
- Ne pas afficher au client les détails d'erreur internes du backend.
- Les actions destructives demandent une confirmation claire et un droit
  serveur ; masquer un bouton ne constitue pas une autorisation.

## Performance et maintenabilité

- Utiliser le chargement différé pour les pages et bibliothèques lourdes.
- Éviter d'augmenter le bundle initial sans mesure avant/après.
- Extraire les pages surdimensionnées en composants et hooks spécialisés.
- Ne pas dupliquer les libellés, formats monétaires ou règles de filtre.

## Validation

```bash
cd 08_FRONTEND
npm ci
npm run build
npm run test:e2e
```

Pour une modification ciblée, exécuter au minimum le build et les scénarios
E2E directement concernés.

