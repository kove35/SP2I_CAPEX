import React from "react";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import { analyzeExcel, syncExcel, validateAiMapping } from "../../services/excelUploadService";

export default function DqePage() {
  const [tab, setTab] = React.useState(new URLSearchParams(window.location.search).get("tab") || "import");
  const [file, setFile] = React.useState(null);
  const [analysis, setAnalysis] = React.useState(null);
  const [syncResult, setSyncResult] = React.useState(null);
  const [validationResult, setValidationResult] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "import");
  }, [window.location.search]);

  const recommendedSheet = analysis?.feuille_recommandee || "-";
  const bestAnalysis = analysis?.analyses?.[0] || {};
  const previewRows = analysis?.lignes_normalisees_preview || [];
  const aiPreview = analysis?.ai_preview || {};
  const aiConfidence = analysis?.ai_confidence || {};
  const aiAnomalies = analysis?.ai_anomalies || [];
  const aiSuggestions = analysis?.ai_suggestions || {};
  const lineCount = bestAnalysis.lignes_detectees || previewRows.length || 0;
  const qualityScore = Math.round(Number(aiPreview.quality_score ?? bestAnalysis.score_dqe ?? 0) * 100);
  const warningCount = bestAnalysis.avertissements?.length || 0;

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    setError("");
    setSyncResult(null);
    setValidationResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".xlsx") && !selectedFile.name.toLowerCase().endsWith(".xlsm")) {
      setFile(null);
      setAnalysis(null);
      setError("Le fichier doit etre un Excel .xlsx ou .xlsm.");
      return;
    }

    setFile(selectedFile);
  };

  const runAnalysis = async () => {
    if (!file) {
      setError("Selectionne d'abord un fichier Excel.");
      return;
    }

    setLoading(true);
    setError("");
    setSyncResult(null);
    try {
      const result = await analyzeExcel(file);
      setAnalysis(result);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  };

  const runValidateMapping = async () => {
    if (!analysis?.file_id) {
      setError("Analyse d'abord un fichier Excel avant validation humaine.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const result = await validateAiMapping(analysis.file_id, bestAnalysis.mapping || []);
      setValidationResult(result);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  };

  const runSync = async () => {
    if (!file) {
      setError("Selectionne d'abord un fichier Excel.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const result = await syncExcel(file);
      setSyncResult(result);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">DQE & Data</p>
        <h1>Import Excel, analyse DQE et qualite des donnees</h1>
      </section>
      <div className="tab-row">
        <button className={tab === "import" ? "active" : ""} onClick={() => setTab("import")} type="button">Import Excel</button>
        <button className={tab === "analysis" ? "active" : ""} onClick={() => setTab("analysis")} type="button">Analyse DQE</button>
        <button className={tab === "mapping" ? "active" : ""} onClick={() => setTab("mapping")} type="button">Normalisation</button>
        <button className={tab === "quality" ? "active" : ""} onClick={() => setTab("quality")} type="button">Qualite donnees</button>
      </div>
      {error ? <div className="app-error">{error}</div> : null}
      <section className="metric-grid">
        <KpiCard label="Fichier" value={file ? "Excel" : "Aucun"} />
        <KpiCard label="Feuille recommandee" value={recommendedSheet} />
        <KpiCard label="Score DQE" value={`${qualityScore}%`} tone={qualityScore >= 80 ? "success" : "warning"} />
        <KpiCard label="Lots detectes" value={aiPreview.lots_detected ?? "-"} />
      </section>
      <section className="cockpit-split">
        <AnalyticsCard title={tab === "mapping" ? "Mapping standard SP2I" : tab === "quality" ? "Controle qualite" : "Preview Excel DQE"} eyebrow="Upload intelligent">
          {tab === "import" ? (
            <div className="excel-upload-zone">
              <label>
                Fichier Excel DQE/BPU
                <input type="file" accept=".xlsx,.xlsm" onChange={handleFileChange} />
              </label>
              <div className="excel-actions">
                <button className="primary-action" type="button" onClick={runAnalysis} disabled={!file || loading}>
                  {loading ? "Analyse..." : "Analyser Excel"}
                </button>
                <button className="primary-action secondary-action" type="button" onClick={runValidateMapping} disabled={!analysis?.file_id || loading}>
                  Valider mapping IA
                </button>
                <button className="primary-action secondary-action" type="button" onClick={runSync} disabled={!file || loading}>
                  Synchroniser PostgreSQL
                </button>
              </div>
              {file ? <p>Fichier selectionne : <strong>{file.name}</strong></p> : <p>Formats acceptes : .xlsx et .xlsm.</p>}
            </div>
          ) : null}

          {tab === "analysis" || tab === "import" ? (
            <>
              <div className="ai-preview-grid">
                <span>Colonnes reconnues <strong>{aiPreview.recognized_columns ?? "-"}</strong></span>
                <span>Colonnes ambigues <strong>{aiPreview.ambiguous_columns ?? "-"}</strong></span>
                <span>Anomalies <strong>{aiPreview.invalid_rows ?? aiAnomalies.length}</strong></span>
                <span>CAPEX detecte <strong>{Number(aiPreview.estimated_capex_detected || 0).toLocaleString("fr-FR")}</strong></span>
              </div>
              <div className="data-table-wrap panel-scroll">
                <table className="data-table">
                  <thead><tr><th>Designation</th><th>Lot</th><th>Famille IA</th><th>Quantite</th><th>PU local</th></tr></thead>
                  <tbody>
                    {previewRows.map((row, index) => (
                      <tr key={row.id_ligne || `${row.designation}-${index}`}>
                        <td>{row.designation || "-"}</td>
                        <td>{row.lot || "-"}</td>
                        <td>{row.famille_ai || row.famille || "-"}</td>
                        <td>{row.quantite || 0}</td>
                        <td>{row.prix_unitaire_ht || row.pu_local || 0}</td>
                      </tr>
                    ))}
                    {!previewRows.length ? <tr><td colSpan="5">Analyse un fichier Excel pour afficher la preview normalisee.</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}

          {tab === "mapping" ? (
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Colonne Excel</th><th>Champ SP2I</th><th>Confiance</th><th>Raison</th></tr></thead>
                <tbody>
                  {(bestAnalysis.mapping || []).map((mapping) => (
                    <tr key={`${mapping.colonne_excel}-${mapping.champ_standard}`}>
                      <td>{mapping.colonne_excel}</td>
                      <td>{mapping.champ_standard}</td>
                      <td>{Math.round(Number(mapping.confiance || 0) * 100)}%</td>
                      <td>{mapping.raison}</td>
                    </tr>
                  ))}
                  {!bestAnalysis.mapping?.length ? <tr><td colSpan="4">Aucun mapping disponible avant analyse Excel.</td></tr> : null}
                </tbody>
              </table>
            </div>
          ) : null}

          {tab === "quality" ? (
            <ul className="signal-list">
              <li>Score DQE : {qualityScore}%.</li>
              <li>Confiance globale IA : {Math.round(Number(aiConfidence.global_confidence || 0) * 100)}%.</li>
              <li>{warningCount} avertissement(s) mapping et {aiAnomalies.length} anomalie(s) detectees.</li>
              <li>Feuille recommandee : {recommendedSheet}.</li>
              <li>{validationResult ? "Mapping valide humainement." : "Validation humaine recommandee avant synchronisation."}</li>
              <li>{syncResult ? "Synchronisation pipeline effectuee." : "Synchronise seulement apres controle de la preview."}</li>
            </ul>
          ) : null}
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Action suivante" eyebrow="Workflow">
            <ul className="signal-list">
              <li>1. Selectionner le fichier Excel DQE/BPU.</li>
              {(aiSuggestions.next_actions || [
                "2. Lancer l'analyse pour verifier feuille, lignes et mapping.",
                "3. Synchroniser PostgreSQL uniquement si la preview est correcte.",
                "4. Lancer ensuite la simulation CAPEX.",
              ]).map((action) => <li key={action}>{action}</li>)}
            </ul>
          </AnalyticsCard>
          <AnalyticsCard title="Statut pipeline" eyebrow="Excel vers SP2I">
            <ul className="signal-list">
              <li>File ID : {analysis?.file_id || "-"}</li>
              <li>Preview IA : {analysis ? "OK" : "en attente"}</li>
              <li>Validation humaine : {validationResult ? "OK" : "non validee"}</li>
              <li>Sync PostgreSQL : {syncResult ? "OK" : "non lancee"}</li>
              <li>Endpoint preview : /api/upload/excel</li>
              <li>Endpoint sync : /api/upload/excel/sync</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
