import React from "react";
import { useQuery } from "@tanstack/react-query";
import AnalyticsCard from "../../ui/AnalyticsCard";
import KpiCard from "../../ui/KpiCard";
import { analyzeExcel, syncExcel, validateAiMapping } from "../../services/excelUploadService";
import { getAnalyticsDataQuality } from "../../services/analyticsService";
import { useAppStore } from "../../store/appStore.jsx";
import { PROJECT_CONTEXT } from "../../utils/businessContext";

const SUPPORTED_UPLOAD_EXTENSIONS = [".xlsx", ".xlsm", ".xls", ".csv"];
const SYNCED_STATUSES = ["SYNCED", "CERTIFIED", "CERTIFIED_WITH_WARNINGS"];
const STATUS_LABELS = {
  NOT_IMPORTED: "Non importe",
  UPLOADED: "Importe",
  ANALYZED: "Analyse",
  MAPPING_VALIDATED: "Correspondance validee",
  SYNCED: "Synchronise",
  CERTIFIED: "Certifie",
  CERTIFIED_WITH_WARNINGS: "Certifie avec points a verifier",
  REVIEW_REQUIRED: "Validation requise",
  REJECTED: "Rejete",
  ARCHIVED: "Archive",
};

function hasSupportedExtension(fileName) {
  const lowerName = fileName.toLowerCase();
  return SUPPORTED_UPLOAD_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
}

function isSuccessResponse(data) {
  return data?.status === "SUCCESS";
}

function getStorageKey(projectId) {
  return `sp2i:dqeVersions:${projectId || PROJECT_CONTEXT.code}`;
}

function getFileExtension(fileName = "") {
  const match = fileName.match(/\.([a-z0-9]+)$/i);
  return match ? match[1].toUpperCase() : "EXCEL";
}

function getSeedVersions(projectId) {
  if (projectId !== PROJECT_CONTEXT.code) return [];
  return [
    {
      id: "seed-dqe-v1",
      project_id: projectId,
      version_number: 1,
      file_name: "DQE_PROJECT_SP2I.xlsx",
      file_type: "XLSX",
      uploaded_by: "SP2I",
      uploaded_at: new Date().toISOString(),
      status: "SYNCED",
      trust_score: 87,
      normalized_lines_count: 46,
      ignored_lines_count: 0,
      data_loss_count: 0,
      integrity_issue_count: 0,
      quality_issue_count: 0,
      review_required_count: 0,
      is_active: true,
      synced_at: new Date().toISOString(),
    },
  ];
}

function readStoredVersions(projectId) {
  try {
    const stored = window.localStorage.getItem(getStorageKey(projectId));
    if (!stored) return getSeedVersions(projectId);
    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed : getSeedVersions(projectId);
  } catch {
    return getSeedVersions(projectId);
  }
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("fr-FR");
}

export default function DqePage() {
  const { state } = useAppStore();
  const projectId = state.activeProject || PROJECT_CONTEXT.code;
  const searchParams = new URLSearchParams(window.location.search);
  const [tab, setTab] = React.useState(searchParams.get("tab") || "import");
  const [file, setFile] = React.useState(null);
  const [pendingFile, setPendingFile] = React.useState(null);
  const [analysis, setAnalysis] = React.useState(null);
  const [syncResult, setSyncResult] = React.useState(null);
  const [validationResult, setValidationResult] = React.useState(null);
  const [dqeVersions, setDqeVersions] = React.useState(() => readStoredVersions(projectId));
  const [currentVersionId, setCurrentVersionId] = React.useState(() => readStoredVersions(projectId).find((item) => item.is_active)?.id || null);
  const [showNewVersionConfirm, setShowNewVersionConfirm] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const dataQuality = useQuery({
    queryKey: ["analytics-data-quality", syncResult?.db_sync?.fact_metre_sql_count || 0],
    queryFn: getAnalyticsDataQuality,
    enabled: ["quality", "history", "sync"].includes(tab),
    staleTime: 30_000,
  });

  React.useEffect(() => {
    setTab(new URLSearchParams(window.location.search).get("tab") || "import");
  }, [window.location.search]);

  React.useEffect(() => {
    const versions = readStoredVersions(projectId);
    setDqeVersions(versions);
    setCurrentVersionId(versions.find((item) => item.is_active)?.id || versions[0]?.id || null);
  }, [projectId]);

  React.useEffect(() => {
    window.localStorage.setItem(getStorageKey(projectId), JSON.stringify(dqeVersions));
  }, [dqeVersions, projectId]);

  const activeVersion = dqeVersions.find((version) => version.is_active) || null;
  const currentVersion = dqeVersions.find((version) => version.id === currentVersionId) || activeVersion || dqeVersions[0] || null;
  const hasDqeVersion = Boolean(currentVersion);
  const hasSyncedVersion = Boolean(activeVersion && SYNCED_STATUSES.includes(activeVersion.status));
  const currentStatus = currentVersion?.status || "NOT_IMPORTED";
  const nextVersionNumber = Math.max(0, ...dqeVersions.map((item) => Number(item.version_number || 0))) + 1;
  const recommendedSheet = analysis?.feuille_recommandee || "-";
  const bestAnalysis = analysis?.analyses?.[0] || {};
  const previewRows = Array.isArray(analysis?.lignes_normalisees_preview)
    ? analysis.lignes_normalisees_preview
    : [];
  const aiPreview = analysis?.ai_preview || {};
  const aiConfidence = analysis?.ai_confidence || {};
  const aiAnomalies = Array.isArray(analysis?.ai_anomalies) ? analysis.ai_anomalies : [];
  const aiSuggestions = analysis?.ai_suggestions || {};
  const lineCount = bestAnalysis.lignes_detectees || previewRows.length || 0;
  const qualityScore = Math.round(Number(aiPreview.quality_score ?? bestAnalysis.score_dqe ?? 0) * 100);
  const recognizedColumns = aiPreview.recognized_columns ?? "-";
  const lotsDetected = aiPreview.lots_detected ?? "-";
  const estimatedBudget = Number(aiPreview.estimated_capex_detected || 0);
  const warningCount = bestAnalysis.avertissements?.length || 0;
  const qualityPayload = dataQuality.data || {};
  const qualityKpis = qualityPayload.kpis || {};
  const qualityMeta = qualityPayload.metadata || {};
  const importHistory = qualityMeta.history || [];
  const pipelineSteps = qualityPayload.charts?.pipeline || [];
  const qualityWarnings = qualityPayload.warnings || [];
  const qualityAnomalies = Array.isArray(qualityPayload.table) ? qualityPayload.table : [];
  const qualityCenterScore = Math.round(Number(qualityKpis.score_qualite ?? qualityScore ?? 0));
  const hasQualityContext = Boolean(analysis || syncResult || activeVersion || dataQuality.data);
  const qualityCenterLabel = hasQualityContext ? `${qualityCenterScore}%` : "Non analyse";
  const capexSource = Number(qualityKpis.capex_source || 0);
  const capexAnalytics = Number(qualityKpis.capex_analytics || 0);
  const capexGapPct = Number(qualityKpis.ecart_capex_pct || 0) * 100;
  const dqeRequiredNotice = searchParams.get("notice") === "dqe-required";
  const displayQualityScore = analysis || syncResult || currentVersion?.trust_score != null ? `${currentVersion?.trust_score ?? qualityScore}%` : "-";
  const importActionLabel = !hasDqeVersion
    ? "Importer le premier DQE"
    : hasSyncedVersion
      ? "Creer une nouvelle version DQE"
      : "Importer une nouvelle version";

  const updateCurrentVersion = React.useCallback((patch) => {
    setDqeVersions((versions) => versions.map((version) => (
      version.id === currentVersionId ? { ...version, ...patch } : version
    )));
  }, [currentVersionId]);

  const createVersionFromFile = React.useCallback((selectedFile, status = "UPLOADED") => {
    const version = {
      id: `dqe-v${Date.now()}`,
      project_id: projectId,
      version_number: Math.max(0, ...dqeVersions.map((item) => Number(item.version_number || 0))) + 1,
      file_name: selectedFile.name,
      file_type: getFileExtension(selectedFile.name),
      uploaded_by: "Utilisateur courant",
      uploaded_at: new Date().toISOString(),
      status,
      trust_score: null,
      normalized_lines_count: null,
      ignored_lines_count: null,
      data_loss_count: null,
      integrity_issue_count: null,
      quality_issue_count: null,
      review_required_count: null,
      is_active: dqeVersions.length === 0,
      synced_at: null,
    };
    setDqeVersions((versions) => [version, ...versions]);
    setCurrentVersionId(version.id);
    setFile(selectedFile);
    setAnalysis(null);
    setSyncResult(null);
    setValidationResult(null);
    return version;
  }, [dqeVersions, projectId]);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];
    setError("");
    setSyncResult(null);
    setValidationResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!hasSupportedExtension(selectedFile.name)) {
      setFile(null);
      setAnalysis(null);
      setError("Le fichier doit etre au format .xlsx, .xlsm, .xls ou .csv.");
      return;
    }

    if (hasSyncedVersion) {
      setPendingFile(selectedFile);
      setShowNewVersionConfirm(true);
      event.target.value = "";
      return;
    }

    createVersionFromFile(selectedFile);
  };

  const confirmNewVersion = () => {
    if (pendingFile) createVersionFromFile(pendingFile);
    setPendingFile(null);
    setShowNewVersionConfirm(false);
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
      console.log("API RESPONSE DQE ANALYZE", result);
      if (!isSuccessResponse(result)) {
        setAnalysis(null);
        setError(result?.message || result?.detail || "Erreur analyse DQE.");
        return;
      }
      setAnalysis(result);
      const resultBestAnalysis = result?.analyses?.[0] || {};
      const resultAiPreview = result?.ai_preview || {};
      const resultScore = Math.round(Number(resultAiPreview.quality_score ?? resultBestAnalysis.score_dqe ?? 0) * 100);
      updateCurrentVersion({
        status: "ANALYZED",
        trust_score: resultScore,
        normalized_lines_count: result?.lignes_normalisees_preview?.length || resultBestAnalysis.lignes_detectees || null,
        ignored_lines_count: result?.parsing_stats?.ignored || null,
        data_loss_count: result?.parsing_stats?.data_loss || null,
        quality_issue_count: resultAiPreview.invalid_rows || null,
        review_required_count: result?.parsing_stats?.review_required || null,
      });
      setError(null);
    } catch (apiError) {
      setError(`Analyse DQE indisponible : ${apiError.message}`);
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
      updateCurrentVersion({ status: "MAPPING_VALIDATED" });
    } catch (apiError) {
      setError(`Validation de la correspondance indisponible : ${apiError.message}`);
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
      console.log("API RESPONSE DQE SYNC", result);
      if (result?.status && result.status !== "SUCCESS" && result.status !== "OK") {
        setError(result?.message || result?.detail || "Erreur synchronisation PostgreSQL.");
        return;
      }
      setSyncResult(result);
      setDqeVersions((versions) => versions.map((version) => (
        version.id === currentVersionId
          ? {
              ...version,
              status: "SYNCED",
              is_active: true,
              synced_at: new Date().toISOString(),
              trust_score: version.trust_score ?? qualityScore,
              normalized_lines_count: result?.db_sync?.fact_metre_sql_count || version.normalized_lines_count,
            }
          : { ...version, is_active: false }
      )));
      setError(null);
    } catch (apiError) {
      setError(`Synchronisation PostgreSQL indisponible : ${apiError.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="cockpit-page cockpit-page-fit">
      <section className="page-hero compact">
        <p className="eyebrow">DQE & donnees projet</p>
        <h1>Importer, verifier et fiabiliser le budget du projet</h1>
      </section>
      {showNewVersionConfirm ? (
        <div className="dqe-version-modal" role="dialog" aria-modal="true" aria-labelledby="dqe-new-version-title">
          <div className="dqe-version-dialog">
            <h2 id="dqe-new-version-title">Creer une nouvelle version DQE ?</h2>
            <p>
              Un DQE est deja associe a ce projet. Le nouvel import creera une nouvelle version sans supprimer
              l'historique existant.
            </p>
            <p>
              Les donnees actuellement synchronisees resteront utilisees tant que la nouvelle version n'est pas validee.
            </p>
            <div className="excel-actions">
              <button className="primary-action secondary-action" type="button" onClick={() => { setShowNewVersionConfirm(false); setPendingFile(null); }}>
                Annuler
              </button>
              <button className="primary-action" type="button" onClick={confirmNewVersion}>
                Creer une nouvelle version
              </button>
            </div>
          </div>
        </div>
      ) : null}
      <div className="tab-row">
        <button className={tab === "import" ? "active" : ""} onClick={() => setTab("import")} type="button">Importer le DQE</button>
        <button className={tab === "analysis" ? "active" : ""} onClick={() => setTab("analysis")} type="button">Analyse DQE</button>
        <button className={tab === "mapping" ? "active" : ""} onClick={() => setTab("mapping")} type="button">Correspondance</button>
        <button className={tab === "sync" ? "active" : ""} onClick={() => setTab("sync")} type="button">Envoyer en base</button>
        <button className={tab === "quality" ? "active" : ""} onClick={() => setTab("quality")} type="button">Qualite donnees</button>
        <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")} type="button">Historique imports</button>
      </div>
      {error ? <div className="app-error">{error}</div> : null}
      {dqeRequiredNotice ? <div className="app-warning">Importez et validez un DQE avant de tester un scenario.</div> : null}
      <section className="metric-grid">
        <KpiCard label="DQE actif" value={activeVersion ? `v${activeVersion.version_number}` : "-"} />
        <KpiCard label="Version en travail" value={currentVersion ? `v${currentVersion.version_number}` : "-"} />
        <KpiCard label="Score confiance" value={displayQualityScore} tone={(currentVersion?.trust_score ?? qualityScore) >= 80 ? "success" : "warning"} />
        <KpiCard label="Statut" value={STATUS_LABELS[currentStatus] || currentStatus} />
      </section>
      <section className="dqe-version-state">
        <AnalyticsCard title="Etat DQE du projet" eyebrow="Versionnement">
          {!hasDqeVersion ? (
            <div className="empty-state compact">
              <strong>Aucun DQE importe pour ce projet.</strong>
              <p>Importez un fichier Excel DQE/BPU pour demarrer l'analyse. Le premier import creera automatiquement DQE v1.</p>
            </div>
          ) : (
            <>
              {hasSyncedVersion ? (
                <p className="dqe-version-notice">
                  Ce DQE est deja synchronise avec la base projet. Un nouvel import creera une nouvelle version et
                  necessitera une nouvelle analyse, une nouvelle validation et une nouvelle synchronisation.
                </p>
              ) : (
                <p className="dqe-version-notice">
                  Un DQE est deja en cours de preparation pour ce projet. Vous pouvez continuer l'analyse ou importer une nouvelle version.
                </p>
              )}
              <div className="dqe-state-grid">
                <span><b>DQE actif</b>{activeVersion?.file_name || "-"}</span>
                <span><b>Version active</b>{activeVersion ? `DQE v${activeVersion.version_number}` : "-"}</span>
                <span><b>Statut</b>{STATUS_LABELS[currentStatus] || currentStatus}</span>
                <span><b>Dernier import</b>{formatDate(currentVersion?.uploaded_at)}</span>
                <span><b>Dernier utilisateur</b>{currentVersion?.uploaded_by || "-"}</span>
                <span><b>Trust score</b>{currentVersion?.trust_score != null ? `${currentVersion.trust_score}/100` : "Non analyse"}</span>
                <span><b>Lignes exploitables</b>{currentVersion?.normalized_lines_count ?? "-"}</span>
                <span><b>Lignes ignorees non critiques</b>{currentVersion?.ignored_lines_count ?? "-"}</span>
                <span><b>Perte stricte</b>{currentVersion?.data_loss_count ?? "-"}</span>
                <span><b>Synchronisation PostgreSQL</b>{currentVersion?.synced_at ? formatDate(currentVersion.synced_at) : "Non effectuee"}</span>
              </div>
            </>
          )}
        </AnalyticsCard>
      </section>
      <section className="cockpit-split">
        <AnalyticsCard title={tab === "mapping" ? "Correspondance des colonnes" : tab === "quality" ? "Centre de controle qualite" : tab === "sync" ? "Envoi controle en base projet" : tab === "history" ? "Historique des imports DQE" : "Apercu du DQE importe"} eyebrow="Import assiste">
          {tab === "import" ? (
            <div className="excel-upload-zone">
              <h3>{importActionLabel}</h3>
              <label>
                Fichier DQE/BPU
                <input type="file" accept=".xlsx,.xlsm,.xls,.csv" onChange={handleFileChange} />
              </label>
              <div className="excel-actions">
                <button className="primary-action" type="button" onClick={runAnalysis} disabled={!file || loading}>
                  {loading ? "Analyse..." : "Analyser Excel"}
                </button>
                <button className="primary-action secondary-action" type="button" onClick={runValidateMapping} disabled={!analysis?.file_id || loading}>
                  Valider la correspondance
                </button>
                <button className="primary-action secondary-action" type="button" onClick={runSync} disabled={!file || !validationResult || loading}>
                  Envoyer en base projet
                </button>
              </div>
              {file ? <p>Fichier selectionne : <strong>{file.name}</strong> - preparation de DQE v{currentVersion?.version_number || nextVersionNumber}.</p> : <p>Formats acceptes : .xlsx, .xlsm, .xls et .csv.</p>}
              {hasSyncedVersion ? (
                <p className="dqe-version-notice">
                  Des scenarios peuvent deja utiliser la version active. Ils restent conserves tant qu'une nouvelle version n'est pas synchronisee.
                </p>
              ) : null}
            </div>
          ) : null}

          {tab === "analysis" || tab === "import" ? (
            <>
              <div className="ai-preview-grid">
                <span>Colonnes reconnues <strong>{recognizedColumns}</strong></span>
                <span>Colonnes ambigues <strong>{aiPreview.ambiguous_columns ?? "-"}</strong></span>
                <span>Anomalies <strong>{aiPreview.invalid_rows ?? aiAnomalies.length}</strong></span>
                <span>Budget detecte <strong>{estimatedBudget.toLocaleString("fr-FR")}</strong></span>
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
                    {!previewRows.length ? <tr><td colSpan="5">Analyse un fichier Excel pour afficher l'apercu nettoye.</td></tr> : null}
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
                  {!bestAnalysis.mapping?.length ? <tr><td colSpan="4">Aucune correspondance disponible avant analyse Excel.</td></tr> : null}
                </tbody>
              </table>
            </div>
          ) : null}

          {tab === "sync" ? (
            <div className="excel-upload-zone">
              <p>Cette action synchronise la version DQE en cours uniquement si le fichier produit un FACT_METRE exploitable.</p>
              <label>
                Fichier DQE/BPU a envoyer
                <input type="file" accept=".xlsx,.xlsm,.xls,.csv" onChange={handleFileChange} />
              </label>
              <div className="excel-actions">
                <button className="primary-action secondary-action" type="button" onClick={runAnalysis} disabled={!file || loading}>
                  Controler avant envoi
                </button>
                <button className="primary-action" type="button" onClick={runSync} disabled={!file || !validationResult || loading}>
                  {loading ? "Envoi..." : "Envoyer en base projet"}
                </button>
              </div>
              <ul className="signal-list">
                <li>Protection active : sync vide ou sans CAPEX positif bloquee.</li>
                <li>Audit cree automatiquement apres synchronisation.</li>
                <li>Dernier statut : {syncResult?.db_sync?.status || syncResult?.status || "non lance"}.</li>
              </ul>
            </div>
          ) : null}

          {tab === "quality" ? (
            <div className="quality-center">
              <div className="ai-preview-grid">
                <span>Qualite donnees <strong>{qualityCenterLabel}</strong></span>
                <span>CAPEX fichier <strong>{capexSource.toLocaleString("fr-FR")}</strong></span>
                <span>CAPEX cockpit <strong>{capexAnalytics.toLocaleString("fr-FR")}</strong></span>
                <span>Ecart financier <strong>{capexGapPct.toFixed(3)}%</strong></span>
              </div>
              <ul className="signal-list">
                <li>Controle financier : tolerance maximale 0,5 % entre le fichier source et FACT_METRE.</li>
                <li>Lignes fichier : {qualityKpis.lignes_excel ?? lineCount} | lignes en base : {qualityKpis.lignes_fact_metre ?? "-"}.</li>
                <li>Classification metier a completer : {qualityKpis.lignes_famille_a_classer ?? "-"} ligne(s).</li>
                <li>Source retenue : {(qualityMeta.source?.source_fact_metre || [recommendedSheet]).join(", ") || "-"}.</li>
                <li>Statut QA : {qualityMeta.qa_status || (qualityWarnings.length ? "WARN" : "PASS")}.</li>
              </ul>
              <div className="data-table-wrap panel-scroll">
                <table className="data-table">
                  <thead><tr><th>Etape</th><th>Lignes</th></tr></thead>
                  <tbody>
                    {pipelineSteps.map((step) => (
                      <tr key={step.label}>
                        <td>{step.label}</td>
                        <td>{Number(step.value || 0).toLocaleString("fr-FR")}</td>
                      </tr>
                    ))}
                    {!pipelineSteps.length ? <tr><td colSpan="2">Aucun controle pipeline disponible pour le moment.</td></tr> : null}
                  </tbody>
                </table>
              </div>
              {qualityWarnings.length ? (
                <div className="app-error">
                  {qualityWarnings.map((warning) => <div key={warning}>{warning}</div>)}
                </div>
              ) : null}
              <div className="data-table-wrap panel-scroll">
                <table className="data-table">
                  <thead><tr><th>Point a controler</th><th>Severite</th><th>Action recommandee</th></tr></thead>
                  <tbody>
                    {qualityAnomalies.slice(0, 12).map((item, index) => (
                      <tr key={`${item.code || item.type || "anomaly"}-${index}`}>
                        <td>{item.message || item.reason || item.code || item.type || "Anomalie detectee"}</td>
                        <td>{item.severity || item.niveau || "A controler"}</td>
                        <td>{item.action || "Verifier la ligne source avant synchronisation."}</td>
                      </tr>
                    ))}
                    {!qualityAnomalies.length ? <tr><td colSpan="3">Aucune anomalie detaillee remontee par le dernier controle.</td></tr> : null}
                  </tbody>
                </table>
              </div>
              {dataQuality.isLoading ? <p>Controle qualite en cours...</p> : null}
              {dataQuality.error ? <p className="app-error">Controle qualite indisponible : {dataQuality.error.message}</p> : null}
            </div>
          ) : null}

          {tab === "history" ? (
            <div className="data-table-wrap panel-scroll">
              <table className="data-table">
                <thead><tr><th>Version</th><th>Fichier</th><th>Date import</th><th>Importe par</th><th>Statut</th><th>Trust score</th><th>Lignes exploitables</th><th>Perte stricte</th><th>Synchronisation</th><th>Actions</th></tr></thead>
                <tbody>
                  {dqeVersions.map((item) => (
                    <tr key={item.id}>
                      <td>DQE v{item.version_number}{item.is_active ? " - actif" : ""}</td>
                      <td>{item.file_name || "-"}</td>
                      <td>{formatDate(item.uploaded_at)}</td>
                      <td>{item.uploaded_by || "-"}</td>
                      <td>{STATUS_LABELS[item.status] || item.status}</td>
                      <td>{item.trust_score != null ? `${item.trust_score}/100` : "-"}</td>
                      <td>{item.normalized_lines_count ?? "-"}</td>
                      <td>{item.data_loss_count ?? "-"}</td>
                      <td>{item.synced_at ? "Synchronise" : "Non effectuee"}</td>
                      <td>
                        <button className="link-button" type="button" onClick={() => { setCurrentVersionId(item.id); setTab("import"); }}>
                          Voir details
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!dqeVersions.length && importHistory.map((item, index) => (
                    <tr key={item.import_id || `${item.fichier}-${item.created_at}`}>
                      <td>v{index + 1}</td>
                      <td>{item.fichier || "-"}</td>
                      <td>{item.created_at ? new Date(item.created_at).toLocaleString("fr-FR") : "-"}</td>
                      <td>-</td>
                      <td>{STATUS_LABELS.SYNCED}</td>
                      <td>{Math.round(Number(item.score_qualite || 0)) || "-"}</td>
                      <td>{Number(item.lignes_fact_metre || 0).toLocaleString("fr-FR")}</td>
                      <td>-</td>
                      <td>Synchronise</td>
                      <td>Rapport qualite</td>
                    </tr>
                  ))}
                  {!dqeVersions.length && !importHistory.length ? <tr><td colSpan="10">Aucun historique persistant disponible avant le prochain envoi en base.</td></tr> : null}
                </tbody>
              </table>
            </div>
          ) : null}
        </AnalyticsCard>
        <aside className="context-panel">
          <AnalyticsCard title="Action suivante" eyebrow="Parcours projet">
            <ul className="signal-list">
              <li>1. {hasDqeVersion ? "Continuer la version DQE en cours ou creer une nouvelle version." : "Importer le premier fichier Excel DQE/BPU."}</li>
              {(aiSuggestions.next_actions || [
                "2. Lancer l'analyse pour verifier feuille, lignes et mapping.",
                "3. Valider la correspondance avant synchronisation PostgreSQL.",
                "4. Synchroniser uniquement la version DQE prete.",
                "5. Lancer ensuite la simulation budgetaire.",
              ]).map((action) => <li key={action}>{action}</li>)}
            </ul>
          </AnalyticsCard>
          <AnalyticsCard title="Statut de l'import" eyebrow="DQE vers SP2I">
            <ul className="signal-list">
              <li>File ID : {analysis?.file_id || "-"}</li>
              <li>Apercu IA : {analysis ? "OK" : "en attente"}</li>
              <li>Validation humaine : {validationResult ? "OK" : "non validee"}</li>
              <li>Envoi en base projet : {syncResult ? "OK" : "non lance"}</li>
              <li>Endpoint preview : /api/upload/excel</li>
              <li>Endpoint sync : /api/upload/excel/sync</li>
            </ul>
          </AnalyticsCard>
        </aside>
      </section>
    </main>
  );
}
