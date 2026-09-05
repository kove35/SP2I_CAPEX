import { demoProjects } from "../services/projectService";

export const PROJECT_CONTEXT = {
  code: "PROJET_MPEMBA",
  label: "Complexe immobilier Mpemba",
  location: "Pointe-Noire, Congo-Brazzaville",
  type: "Projet immobilier residentiel",
  status: "Projet actif",
};

export const PROJECT_MPEMBA_KEY = PROJECT_CONTEXT.code;

function isMpembaKey(value) {
  const key = String(value || "").trim().toLowerCase();
  return key === PROJECT_CONTEXT.code.toLowerCase() || key === "projet-mpemba" || key === "projet-mpemba-demo";
}

function readableProjectName(value) {
  const code = String(value || "").trim();
  if (!code) return "";
  // Identifiant numerique ou technique : nom lisible sans inventer de donnee.
  return /^\d+$/.test(code) ? `Projet ${code}` : code;
}

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

export function getProjectContext(projectCodeOrDetails) {
  if (projectCodeOrDetails && typeof projectCodeOrDetails === "object") {
    const details = projectCodeOrDetails;
    const code = details.workspace_key || details.code || details.id || "";
    const base = isMpembaKey(code) ? PROJECT_CONTEXT : {};
    return {
      ...base,
      ...details,
      code,
      label: details.name || details.label || (isMpembaKey(code) ? PROJECT_CONTEXT.label : readableProjectName(code)),
      location: [details.city, details.country, details.location].filter(Boolean).join(", "),
      type: details.type || "",
      status: details.status || "",
    };
  }

  const codeOrId = String(projectCodeOrDetails || "");
  const fallbackProject = demoProjects.find((project) =>
    [project.workspace_key, project.id, project.name].includes(codeOrId)
  );
  const isMpemba = isMpembaKey(codeOrId) || fallbackProject?.workspace_key === PROJECT_MPEMBA_KEY;

  return {
    ...(isMpemba ? PROJECT_CONTEXT : {}),
    code: codeOrId || (isMpemba ? PROJECT_CONTEXT.code : ""),
    label: fallbackProject?.name || (isMpemba ? PROJECT_CONTEXT.label : readableProjectName(codeOrId)),
    location: fallbackProject ? [fallbackProject.city, fallbackProject.country].filter(Boolean).join(", ") : "",
    type: fallbackProject?.type || "",
    status: fallbackProject?.status || "",
    ...(fallbackProject ? { trust_score: fallbackProject.trust_score } : {}),
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
    risk: "Risque à évaluer",
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
