import React from "react";
import { ArrowRight, CheckCircle2, Download, Sparkles, TriangleAlert } from "lucide-react";
import { exportProcurementWorkbook } from "../../../services/projectService";

function navigate(route) {
  window.history.pushState({}, "", route);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export default function ApprovisionnementCopilot({ project, workflow, recommendations = [], alerts = [] }) {
  const [notice, setNotice] = React.useState("");
  const [exporting, setExporting] = React.useState(false);
  const primaryAction = workflow?.primary_action || { label: "Ouvrir Approvisionnement", route: "/app/procurement" };
  const procurementReady = ["READY", "EXPORTABLE"].includes(workflow?.procurement?.status);

  const handleExport = async () => {
    setExporting(true);
    setNotice("");
    try {
      await exportProcurementWorkbook(project?.id, project?.name || "Projet");
      setNotice("Dossier achat exporté.");
    } catch {
      setNotice("Export backend indisponible pour le moment. Le dossier reste consultable dans le cockpit.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <aside className="appro-copilot">
      <section className="appro-copilot-card hero">
        <span><Sparkles size={15} /> Copilote Approvisionnement SP2I</span>
        <strong>{procurementReady ? "Approvisionnement prêt à connecter au chantier" : "Décisions achat à sécuriser"}</strong>
        <p>{workflow?.procurement?.message || "Pilotez les commandes, fournisseurs, risques et livraisons du projet actif."}</p>
        <button type="button" onClick={() => navigate(primaryAction.route || "/app/procurement")}>
          {primaryAction.label || "Ouvrir Approvisionnement"} <ArrowRight size={16} />
        </button>
      </section>

      <section className="appro-copilot-card">
        <span>Recommandations IA</span>
        <ul className="appro-copilot-list">
          {recommendations.map((recommendation, index) => (
            <li key={recommendation}>
              {index === 1 && alerts.length ? <TriangleAlert size={15} /> : <CheckCircle2 size={15} />}
              <span>{recommendation}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="appro-copilot-card">
        <span>Actions dossier</span>
        <button type="button" className="secondary" onClick={() => navigate("/app/procurement")}>Ouvrir opérations achat</button>
        <button type="button" className="secondary" onClick={() => navigate("/app/site?tab=planning")}>Voir exécution chantier</button>
        <button type="button" className="secondary" disabled={exporting} onClick={handleExport}>
          <Download size={15} /> {exporting ? "Export..." : "Exporter dossier achat"}
        </button>
        {notice ? <small>{notice}</small> : null}
      </section>
    </aside>
  );
}
