import React from "react";
import { AlertTriangle, ClipboardCheck, LockKeyhole, Route } from "lucide-react";

function decisionText(reference) {
  const parts = [];
  if (reference.confidenceLevel === "LOW") {
    parts.push("les donnees fournisseur ou prix ne sont pas assez verifiees");
  }
  if (reference.driftLevel === "CRITICAL" || reference.driftLevel === "HIGH") {
    parts.push("les prix semblent eloignes du marche local");
  }
  if (reference.decisionBlocker === "BLOCK_IMPORT") {
    parts.push("l'importation n'est pas autorisee a ce stade");
  }
  if (reference.technicalValidation !== "VERIFIED") {
    parts.push("un controle technique reste necessaire");
  }
  return parts.length
    ? `Cette reference doit etre verifiee car ${parts.join(", ")}.`
    : "Cette reference reste a controler avant decision finale.";
}

function escalationText(level) {
  const map = {
    SENIOR_PROCUREMENT_APPROVAL: "Un responsable achat doit valider avant toute decision.",
    DOUBLE_VALIDATION: "Deux personnes doivent verifier le dossier avant decision.",
    SENIOR_REVIEW: "Une validation superieure est necessaire.",
    PROCUREMENT_REVIEW: "Un acheteur doit verifier les conditions d'achat.",
    STANDARD_REVIEW: "Une verification standard suffit pour avancer.",
  };
  return map[level] || "Une validation humaine est requise.";
}

export default function GovernanceExplainabilityPanel({ reference }) {
  if (!reference) {
    return (
      <aside className="governance-panel explainability-panel">
        <header><span>Explication metier</span><strong>Aucune reference selectionnee</strong></header>
      </aside>
    );
  }

  const cards = [
    { icon: LockKeyhole, title: "Ce qui bloque", text: reference.decisionBlocker === "BLOCK_IMPORT" ? "L'importation n'est pas autorisee tant que le fournisseur, le prix d'achat et le prix local ne sont pas confirmes." : "La reference doit etre relue par une personne avant toute decision.", tone: "critical" },
    { icon: Route, title: "Qui doit intervenir", text: escalationText(reference.escalationLevel), tone: reference.escalationLevel === "STANDARD_REVIEW" ? "medium" : "critical" },
    { icon: AlertTriangle, title: "Pourquoi c'est risque", text: decisionText(reference), tone: "warning" },
    { icon: ClipboardCheck, title: "Action conseillee", text: "Verifier le fournisseur, comparer le prix au marche local, puis ajouter un commentaire de validation.", tone: "info" },
  ];

  return (
    <aside className="governance-panel explainability-panel">
      <header>
        <span>Explication metier</span>
        <strong>{reference.referenceId}</strong>
      </header>
      <p className="explainability-summary">{decisionText(reference)}</p>
      <div className="explainability-cards">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article className={`explainability-card ${card.tone}`} key={card.title}>
              <Icon size={17} />
              <div>
                <b>{card.title}</b>
                <small>{card.text}</small>
              </div>
            </article>
          );
        })}
      </div>
    </aside>
  );
}
