import React from "react";

const requiredFields = ["name", "client_name", "city", "country", "currency", "project_manager"];

export default function ProjectSetupWizard({ project, onClose, onSave, onImportDqe }) {
  const [form, setForm] = React.useState(() => ({
    name: project?.name || "",
    client_name: project?.client_name || "",
    city: project?.city || "",
    country: project?.country || "Congo-Brazzaville",
    currency: project?.currency || "FCFA",
    project_type: project?.project_type || "Etablissement de sante",
    project_manager: project?.project_manager || "",
    target_budget: project?.target_budget || "",
    vat_mode: project?.vat_mode || "HT",
    reference_exchange_rate: project?.reference_exchange_rate || "",
    default_transport_rate: project?.default_transport_rate || "12",
    default_customs_rate: project?.default_customs_rate || "15",
    default_insurance_rate: project?.default_insurance_rate || "2",
    default_import_margin: project?.default_import_margin || "5",
    minimum_saving_threshold: project?.minimum_saving_threshold || "8",
    planned_start_date: project?.planned_start_date || "",
    target_delivery_date: project?.target_delivery_date || "",
    site_storage_capacity: project?.site_storage_capacity || "",
    critical_lots: project?.critical_lots || "",
    constraints_notes: project?.constraints_notes || "",
  }));

  const completion = Math.round((requiredFields.filter((field) => String(form[field] || "").trim()).length / requiredFields.length) * 100);
  const isConfigured = completion === 100;

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const save = () => {
    onSave?.({
      ...project,
      ...form,
      setup_status: isConfigured ? "CONFIGURED" : "CONFIG_REQUIRED",
      workflow_status: isConfigured ? "DQE_REQUIRED" : "CONFIG_REQUIRED",
      setup_completion_percent: completion,
      setup_completed_at: isConfigured ? new Date().toISOString() : project?.setup_completed_at,
    });
  };

  return (
    <div className="project-setup-overlay" role="presentation" onClick={onClose}>
      <section className="project-setup-dialog" role="dialog" aria-modal="true" aria-label="Configuration projet" data-testid="project-setup-wizard" onClick={(event) => event.stopPropagation()}>
        <header>
          <div>
            <span>Configuration projet</span>
            <h2>{project?.name || "Nouveau projet CAPEX"}</h2>
            <p>Renseignez les parametres minimums pour demarrer le workflow CAPEX sans bloquer les champs optionnels.</p>
          </div>
          <button type="button" onClick={onClose}>Fermer</button>
        </header>

        <div className="project-setup-progress">
          <strong>{completion}%</strong>
          <span>{isConfigured ? "Configuration minimum complete" : "Configuration partielle"}</span>
          <i style={{ width: `${completion}%` }} />
        </div>

        <div className="project-setup-grid">
          <fieldset>
            <legend>1. Informations generales</legend>
            <label>Nom du projet<input value={form.name} onChange={(event) => update("name", event.target.value)} /></label>
            <label>Organisation / client<input value={form.client_name} onChange={(event) => update("client_name", event.target.value)} /></label>
            <label>Ville<input value={form.city} onChange={(event) => update("city", event.target.value)} /></label>
            <label>Pays<input value={form.country} onChange={(event) => update("country", event.target.value)} /></label>
            <label>Type de projet<input value={form.project_type} onChange={(event) => update("project_type", event.target.value)} /></label>
            <label>Responsable projet<input value={form.project_manager} onChange={(event) => update("project_manager", event.target.value)} /></label>
          </fieldset>

          <fieldset>
            <legend>2. Parametres financiers</legend>
            <label>Devise projet<input value={form.currency} onChange={(event) => update("currency", event.target.value)} /></label>
            <label>Budget cible<input value={form.target_budget} onChange={(event) => update("target_budget", event.target.value)} /></label>
            <label>TVA / HT<input value={form.vat_mode} onChange={(event) => update("vat_mode", event.target.value)} /></label>
            <label>Taux de change reference<input value={form.reference_exchange_rate} onChange={(event) => update("reference_exchange_rate", event.target.value)} /></label>
            <label>Seuil economie minimum %<input value={form.minimum_saving_threshold} onChange={(event) => update("minimum_saving_threshold", event.target.value)} /></label>
          </fieldset>

          <fieldset>
            <legend>3. CAPEX / import</legend>
            <label>Transport %<input value={form.default_transport_rate} onChange={(event) => update("default_transport_rate", event.target.value)} /></label>
            <label>Douane %<input value={form.default_customs_rate} onChange={(event) => update("default_customs_rate", event.target.value)} /></label>
            <label>Assurance %<input value={form.default_insurance_rate} onChange={(event) => update("default_insurance_rate", event.target.value)} /></label>
            <label>Marge import %<input value={form.default_import_margin} onChange={(event) => update("default_import_margin", event.target.value)} /></label>
          </fieldset>

          <fieldset>
            <legend>4. Chantier</legend>
            <label>Date debut prevue<input type="date" value={form.planned_start_date} onChange={(event) => update("planned_start_date", event.target.value)} /></label>
            <label>Date livraison cible<input type="date" value={form.target_delivery_date} onChange={(event) => update("target_delivery_date", event.target.value)} /></label>
            <label>Capacite stockage site<input value={form.site_storage_capacity} onChange={(event) => update("site_storage_capacity", event.target.value)} /></label>
            <label>Lots critiques<input value={form.critical_lots} onChange={(event) => update("critical_lots", event.target.value)} /></label>
            <label>Contraintes chantier<textarea value={form.constraints_notes} onChange={(event) => update("constraints_notes", event.target.value)} /></label>
          </fieldset>
        </div>

        <footer>
          <button type="button" className="secondary-action primary-action" onClick={onClose}>Configurer plus tard</button>
          <button type="button" className="secondary-action primary-action" onClick={() => { save(); onImportDqe?.(); }}>Importer maintenant</button>
          <button type="button" className="primary-action" onClick={save}>Enregistrer la configuration</button>
        </footer>
      </section>
    </div>
  );
}
