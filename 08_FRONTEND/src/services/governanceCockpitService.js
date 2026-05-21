import { request } from "./apiClient";

const FAMILY_COUNTS = {
  ELECTRICITE: 65,
  HVAC: 8,
  MENUISERIE_ALU: 41,
  PLOMBERIE: 121,
};

const FAMILY_STATUS = {
  ELECTRICITE: { status: "HIGH_RISK", readiness: 59.2, procurement: 41.5, drift: 32, confidence: 53 },
  HVAC: { status: "HIGH_RISK", readiness: 54.8, procurement: 39.4, drift: 41, confidence: 48 },
  MENUISERIE_ALU: { status: "BLOCKED", readiness: 58.6, procurement: 47.7, drift: 76, confidence: 68 },
  PLOMBERIE: { status: "BLOCKED", readiness: 48.5, procurement: 23, drift: 55, confidence: 47 },
};

const ESCALATIONS = [
  ["SENIOR_PROCUREMENT_APPROVAL", 93],
  ["PROCUREMENT_REVIEW", 83],
  ["SENIOR_REVIEW", 43],
  ["DOUBLE_VALIDATION", 13],
  ["STANDARD_REVIEW", 3],
];

const PRIORITIES = [
  ["CRITICAL", 149],
  ["HIGH", 83],
  ["MEDIUM", 3],
];

const BLOCKERS = ["BLOCK_IMPORT", "REVIEW_REQUIRED", "HIGH_RISK", "TECHNICAL_VALIDATION_REQUIRED"];

function distributeSequence(distribution) {
  return distribution.flatMap(([label, count]) => Array.from({ length: count }, () => label));
}

function familyForIndex(index) {
  let offset = 0;
  for (const [family, count] of Object.entries(FAMILY_COUNTS)) {
    if (index < offset + count) return family;
    offset += count;
  }
  return "PLOMBERIE";
}

function blockerFor(family, index) {
  if (family === "ELECTRICITE") return index % 5 === 0 ? "HIGH_RISK" : "BLOCK_IMPORT";
  if (family === "HVAC") return index % 3 === 0 ? "HIGH_RISK" : "REVIEW_REQUIRED";
  if (family === "MENUISERIE_ALU") return index % 4 === 0 ? "HIGH_RISK" : index % 2 === 0 ? "BLOCK_IMPORT" : "REVIEW_REQUIRED";
  return index % 5 === 0 ? "TECHNICAL_VALIDATION_REQUIRED" : index % 2 === 0 ? "BLOCK_IMPORT" : "REVIEW_REQUIRED";
}

function confidenceFor(family, index) {
  if (family === "MENUISERIE_ALU") return index % 19 === 0 ? "LOW" : "MEDIUM";
  if (family === "HVAC") return index % 3 === 0 ? "MEDIUM" : "LOW";
  if (family === "ELECTRICITE") return index % 13 === 0 ? "MEDIUM" : "LOW";
  return index % 3 === 0 ? "MEDIUM" : "LOW";
}

function driftFor(family, index) {
  if (family === "ELECTRICITE") return index % 7 === 0 ? "HIGH" : "CRITICAL";
  if (family === "HVAC") return index % 3 === 0 ? "CRITICAL" : index % 2 === 0 ? "HIGH" : "MEDIUM";
  if (family === "MENUISERIE_ALU") return index % 20 === 0 ? "HIGH" : "MEDIUM";
  return index % 4 === 0 ? "MEDIUM" : "HIGH";
}

function badgeFromConfidence(level) {
  if (level === "HIGH") return "GREEN";
  if (level === "MEDIUM") return "ORANGE";
  return "RED";
}

function badgeFromRisk(level) {
  if (level === "CRITICAL" || level === "BLOCK_IMPORT") return "DARK_RED";
  if (level === "HIGH" || level === "HIGH_RISK" || level === "TECHNICAL_VALIDATION_REQUIRED") return "RED";
  if (level === "MEDIUM" || level === "REVIEW_REQUIRED") return "ORANGE";
  return "GREEN";
}

function buildReferences() {
  const priorities = distributeSequence(PRIORITIES);
  const escalations = distributeSequence(ESCALATIONS);
  return Array.from({ length: 235 }, (_, index) => {
    const family = familyForIndex(index);
    const familyIndex = Object.keys(FAMILY_COUNTS).indexOf(family) + 1;
    const localIndex = index + 1;
    const priority = priorities[index] || "MEDIUM";
    const escalation = escalations[index] || "STANDARD_REVIEW";
    const blocker = blockerFor(family, index);
    const confidence = confidenceFor(family, index);
    const drift = driftFor(family, index);
    const technical = index % 11 === 0 ? "REJECTED" : "PARTIAL";
    const explanation = [
      priority === "CRITICAL" ? "Reference critique" : "Reference a verifier",
      confidence === "LOW" ? "donnees peu fiables" : "donnees partiellement verifiees",
      drift === "CRITICAL" ? "prix tres eloignes du marche" : drift === "HIGH" ? "prix eloignes du marche" : "prix a comparer au marche local",
      blocker === "BLOCK_IMPORT" ? "importation non autorisee" : blocker === "HIGH_RISK" ? "double verification obligatoire" : "verification achat necessaire",
    ].join(" : ");
    return {
      referenceId: `${family.slice(0, 3)}-GOV-${String(localIndex).padStart(4, "0")}`,
      family,
      designation: `${family.replace("_", " ")} reference gouvernee ${localIndex}`,
      familyStatus: FAMILY_STATUS[family].status,
      readinessScore: FAMILY_STATUS[family].readiness,
      confidenceLevel: confidence,
      procurementScore: FAMILY_STATUS[family].procurement,
      driftLevel: drift,
      technicalValidation: technical,
      decisionBlocker: blocker,
      reviewPriority: priority,
      reviewStatus: "PENDING",
      escalationLevel: escalation,
      governanceAlert: priority,
      driftAlert: drift === "CRITICAL" ? "CRITICAL" : drift === "HIGH" ? "HIGH" : "MEDIUM",
      procurementAlert: blocker === "BLOCK_IMPORT" ? "CRITICAL" : blocker === "HIGH_RISK" ? "HIGH" : "MEDIUM",
      technicalAlert: technical === "REJECTED" ? "CRITICAL" : "HIGH",
      confidenceBadge: badgeFromConfidence(confidence),
      procurementBadge: badgeFromRisk(blocker),
      driftBadge: badgeFromRisk(drift),
      riskBadge: badgeFromRisk(blocker),
      reviewBadge: badgeFromRisk(priority),
      manualValidationRequired: true,
      explanation: `${explanation}. Une personne doit verifier avant decision.`,
      reviewer: "UNASSIGNED",
      supplier: familyIndex % 2 ? "Fournisseur a verifier" : "Benchmark local a confirmer",
      benchmark: confidence === "LOW" ? "LOW" : "MEDIUM",
    };
  });
}

function summarizeByFamily(references) {
  return Object.entries(FAMILY_COUNTS).map(([family]) => {
    const rows = references.filter((row) => row.family === family);
    const status = FAMILY_STATUS[family];
    return {
      family,
      familyStatus: status.status,
      readinessScore: status.readiness,
      reviewRequiredCount: rows.filter((row) => row.reviewStatus === "PENDING").length,
      blockImportCount: rows.filter((row) => row.decisionBlocker === "BLOCK_IMPORT").length,
      driftCriticalCount: rows.filter((row) => row.driftLevel === "CRITICAL").length,
      verifiedReferenceCount: rows.filter((row) => row.confidenceLevel === "HIGH").length,
      highRiskCount: rows.filter((row) => row.decisionBlocker === "HIGH_RISK").length,
      procurementRisk: status.procurement,
      driftScore: status.drift,
      confidenceScore: status.confidence,
    };
  });
}

function buildEscalations(references) {
  return ESCALATIONS.map(([level]) => {
    const rows = references.filter((row) => row.escalationLevel === level);
    return {
      level,
      volume: rows.length,
      critical: rows.filter((row) => row.reviewPriority === "CRITICAL").length,
      high: rows.filter((row) => row.reviewPriority === "HIGH").length,
      severity: level === "SENIOR_PROCUREMENT_APPROVAL" ? "CRITICAL" : level === "DOUBLE_VALIDATION" || level === "SENIOR_REVIEW" ? "HIGH" : "MEDIUM",
    };
  });
}

function buildWorkflow(references) {
  return ["PENDING", "IN_REVIEW", "ESCALATED", "APPROVED", "REJECTED", "NEEDS_MORE_DATA"].map((status) => ({
    status,
    count: references.filter((row) => row.reviewStatus === status).length,
    critical: references.filter((row) => row.reviewStatus === status && row.reviewPriority === "CRITICAL").length,
  }));
}

function buildAuditTimeline(references) {
  return references.slice(0, 18).map((row, index) => ({
    id: `AUD-${String(index + 1).padStart(5, "0")}`,
    date: "2026-05-21",
    eventType: "REVIEW_QUEUE_CREATED",
    referenceId: row.referenceId,
    family: row.family,
    actor: "SYSTEM_GOVERNANCE_WORKBENCH",
    decision: row.reviewStatus,
    justification: row.explanation,
    riskAccepted: false,
  }));
}

function buildGovernanceCockpitData() {
  const references = buildReferences();
  return {
    metadata: {
      generatedAt: "2026-05-21T16:39:31",
      source: "governance-cockpit-dataset-v1",
      mode: "manual-supervision",
    },
    kpis: {
      globalGovernanceScore: 55.27,
      globalProcurementScore: 37.88,
      globalConfidenceScore: 51.34,
      globalDriftScore: 51.06,
      globalTcoScore: 81.25,
      globalReviewBacklog: 235,
      globalEscalationCount: 232,
      globalBlockImportCount: references.filter((row) => row.decisionBlocker === "BLOCK_IMPORT").length,
      globalHighRiskCount: references.filter((row) => row.decisionBlocker === "HIGH_RISK").length,
    },
    references,
    familyKpis: summarizeByFamily(references),
    escalations: buildEscalations(references),
    workflow: buildWorkflow(references),
    auditTimeline: buildAuditTimeline(references),
    badges: {
      GREEN: "Valide humainement ou stable",
      ORANGE: "Revue requise",
      RED: "Risque eleve",
      DARK_RED: "Critique ou bloque",
    },
  };
}

export async function getGovernanceCockpit() {
  try {
    return await request({ url: "/governance/cockpit", method: "GET" });
  } catch (error) {
    console.info("Governance cockpit API indisponible, utilisation du dataset V1 prepare.", error.message);
    return buildGovernanceCockpitData();
  }
}
