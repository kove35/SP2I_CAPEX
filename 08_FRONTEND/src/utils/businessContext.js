export const PROJECT_CONTEXT = {
  code: "Pointe-Noire CAPEX",
  label: "Centre medical Pointe-Noire",
  location: "Pointe-Noire, Congo-Brazzaville",
  type: "Etablissement de sante",
  status: "Projet actif",
};

export const SCENARIO_OPTIONS = [
  {
    code: "IMPORT_OPTIMIZATION",
    label: "Optimisation import",
    description: "Maximiser les economies sur les lots importables.",
    gain: "Gain potentiel eleve",
    risk: "Risque moyen",
    tone: "success",
  },
  {
    code: "BUDGET_REDUCTION",
    label: "Reduction budget",
    description: "Prioriser les baisses de cout sans fragiliser le planning.",
    gain: "Economies fortes",
    risk: "Risque maitrise",
    tone: "success",
  },
  {
    code: "LOCAL_IMPORT_BALANCE",
    label: "Equilibre local/import",
    description: "Conserver un mix prudent entre achats locaux et import.",
    gain: "Gain equilibre",
    risk: "Risque modere",
    tone: "neutral",
  },
  {
    code: "LOGISTICS_SECURITY",
    label: "Securisation logistique",
    description: "Reduire les risques de livraison et de retard chantier.",
    gain: "Gain planning",
    risk: "Risque faible",
    tone: "warning",
  },
  {
    code: "PRUDENT_STRATEGY",
    label: "Strategie prudente",
    description: "Favoriser la stabilite fournisseur et la surete du projet.",
    gain: "Gain selectif",
    risk: "Risque faible",
    tone: "neutral",
  },
];

const TECHNICAL_SCENARIO_PATTERNS = [/FRONT_/i, /_TEST/i, /\bTEST\b/i, /\bDEV\b/i, /SAAS_/i];

export function getProjectContext(projectCode) {
  return {
    ...PROJECT_CONTEXT,
    code: projectCode || PROJECT_CONTEXT.code,
  };
}

export function getScenarioContext(scenarioCode) {
  const normalizedCode = String(scenarioCode || "").trim();
  const direct = SCENARIO_OPTIONS.find((scenario) => scenario.code === normalizedCode);
  if (direct) return direct;

  if (!normalizedCode || TECHNICAL_SCENARIO_PATTERNS.some((pattern) => pattern.test(normalizedCode))) {
    return SCENARIO_OPTIONS[0];
  }

  return {
    code: normalizedCode,
    label: toBusinessScenarioLabel(normalizedCode),
    description: "Simulation budgetaire personnalisee.",
    gain: "Gain a confirmer",
    risk: "Risque a evaluer",
    tone: "neutral",
  };
}

export function toBusinessScenarioLabel(value) {
  const code = String(value || "").trim();
  if (!code) return SCENARIO_OPTIONS[0].label;
  if (TECHNICAL_SCENARIO_PATTERNS.some((pattern) => pattern.test(code))) return SCENARIO_OPTIONS[0].label;
  return code
    .toLowerCase()
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function getScenarioCodeFromLabel(label) {
  return SCENARIO_OPTIONS.find((scenario) => scenario.label === label)?.code || label;
}
