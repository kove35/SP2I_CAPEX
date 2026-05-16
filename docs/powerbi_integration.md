# Integration Power BI

Power BI reste la couche analytique strategique principale.

## Role de React

React fournit :

```text
navigation cockpit
selection projet
selection scenario
lancement workflow
suivi operationnel
integration embedded
```

## Role de Power BI

Power BI fournit :

```text
dashboard direction
dashboard CAPEX
dashboard procurement
dashboard logistics
dashboard chantier
dashboard risques
dashboard investissements
```

## Page frontend

La page est :

```text
/app/analytics
```

Pour passer en Power BI Embedded reel, il faudra fournir :

```text
workspaceId
reportId
embedUrl
accessToken
```

Le placeholder actuel reserve la structure UX sans dupliquer les analytics dans
React.
