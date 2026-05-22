import React from "react";

function money(value) {
  return Number(value || 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 });
}

function percent(value) {
  if (!Number.isFinite(value)) return "-";
  return `${value.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`;
}

function readNumber(...values) {
  const value = values.find((item) => item !== undefined && item !== null && item !== "");
  return Number(value || 0);
}

function decisionLabel(value) {
  const decision = String(value || "").toUpperCase();
  if (decision === "IMPORT") return "Importer";
  if (decision === "LOCAL") return "Acheter local";
  if (decision === "MIXTE") return "A arbitrer";
  if (decision === "REVIEW_REQUIRED") return "Validation requise";
  if (decision === "BLOCKED") return "Bloquant";
  return value || "A analyser";
}

function decisionClass(value) {
  const decision = String(value || "").toLowerCase().replaceAll("_", "-");
  if (decision === "mixte") return "review-required";
  return decision || "pending";
}

function buildJustification(row, savingRate) {
  const decision = String(row.decision_finale || row.decision_import || "").toUpperCase();
  const risk = String(row.risk_level || "").toLowerCase();
  if (decision === "IMPORT") return "Import recommande car l'economie nette est superieure au seuil.";
  if (decision === "LOCAL") return "Achat local recommande car le gain import reste insuffisant ou trop risque.";
  if (decision === "MIXTE") return "A arbitrer : economie positive mais delai ou risque logistique a confirmer.";
  if (decision === "REVIEW_REQUIRED") return "Validation requise avant decision projet.";
  if (risk.includes("eleve") || risk.includes("high")) return "Risque eleve : controle achat ou technique recommande.";
  if (savingRate > 0) return "Economie detectee, decision a confirmer par l'equipe projet.";
  return "Donnees insuffisantes pour justifier automatiquement la decision.";
}

export default function SimulationTable({ rows = [] }) {
  return (
    <div className="analytics-table-wrap">
      <table className="analytics-table">
        <thead>
          <tr>
            <th>Produit</th>
            <th>Famille</th>
            <th>Quantite</th>
            <th>Cout local</th>
            <th>Cout import</th>
            <th>Decision</th>
            <th>Economie</th>
            <th>Taux economie</th>
            <th>Risque</th>
            <th>Justification</th>
            <th>Container</th>
            <th>ETA</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const localCost = readNumber(row.cout_local, row.prix_local, row.capex_local, row.prix_total_ht);
            const importCost = readNumber(row.cout_import, row.landed_cost_chine, row.capex_import, row.capex_chine);
            const saving = readNumber(row.economie_nette, row.gain_net);
            const savingRate = localCost ? (saving / localCost) * 100 : NaN;
            const decision = row.decision_finale || row.decision_import;
            return (
              <tr key={row.id_ligne || row.designation}>
                <td>{row.designation || "-"}</td>
                <td>{row.famille || row.famille_ai || "-"}</td>
                <td>{row.quantite ?? row.qte ?? "-"}</td>
                <td>{localCost ? `${money(localCost)} FCFA` : "-"}</td>
                <td>{importCost ? `${money(importCost)} FCFA` : "-"}</td>
                <td><span className={`decision-badge ${decisionClass(decision)}`}>{decisionLabel(decision)}</span></td>
                <td>{saving ? `${money(saving)} FCFA` : "-"}</td>
                <td>{percent(savingRate)}</td>
                <td>{row.risk_level || "A analyser"}</td>
                <td>{row.justification || buildJustification(row, Number.isFinite(savingRate) ? savingRate : 0)}</td>
                <td>{row.container_strategy || "-"}</td>
                <td>{row.lead_time_total || row.lead_time_days || 0} j</td>
              </tr>
            );
          })}
          {!rows.length ? (
            <tr>
              <td colSpan="12">Aucune simulation lancee pour ce projet.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
