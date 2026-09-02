import React from "react";
import { LockKeyhole, X } from "lucide-react";
import { changePassword, getStoredSession } from "../services/authService";

export default function AccountSecurityControl() {
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState({ current_password: "", new_password: "", confirmation: "" });
  const [status, setStatus] = React.useState({ type: "", message: "" });
  const [saving, setSaving] = React.useState(false);
  const session = getStoredSession();

  if (!session?.access_token || session.token_type !== "bearer") {
    return null;
  }

  async function submit(event) {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    if (form.new_password !== form.confirmation) {
      setStatus({ type: "error", message: "Les nouveaux mots de passe ne correspondent pas." });
      return;
    }
    setSaving(true);
    try {
      await changePassword({
        current_password: form.current_password,
        new_password: form.new_password,
      });
      setForm({ current_password: "", new_password: "", confirmation: "" });
      setStatus({ type: "success", message: "Mot de passe modifié avec succès." });
    } catch (error) {
      setStatus({
        type: "error",
        message: error?.message || "Impossible de modifier le mot de passe.",
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <button
        className="icon-button"
        type="button"
        title="Sécurité du compte"
        aria-label="Sécurité du compte"
        onClick={() => setOpen(true)}
      >
        <LockKeyhole size={18} />
      </button>
      {open ? (
        <div className="account-security-overlay" role="presentation">
          <section className="account-security-dialog" role="dialog" aria-modal="true" aria-labelledby="account-security-title">
            <header>
              <div>
                <h2 id="account-security-title">Sécurité du compte</h2>
                <p>{session?.user?.email || "Compte SP2I"}</p>
              </div>
              <button className="icon-button" type="button" aria-label="Fermer" onClick={() => setOpen(false)}>
                <X size={18} />
              </button>
            </header>
            <form onSubmit={submit}>
              <label>
                Mot de passe actuel
                <input
                  type="password"
                  autoComplete="current-password"
                  minLength={12}
                  required
                  value={form.current_password}
                  onChange={(event) => setForm((current) => ({ ...current, current_password: event.target.value }))}
                />
              </label>
              <label>
                Nouveau mot de passe
                <input
                  type="password"
                  autoComplete="new-password"
                  minLength={12}
                  required
                  value={form.new_password}
                  onChange={(event) => setForm((current) => ({ ...current, new_password: event.target.value }))}
                />
              </label>
              <label>
                Confirmer le nouveau mot de passe
                <input
                  type="password"
                  autoComplete="new-password"
                  minLength={12}
                  required
                  value={form.confirmation}
                  onChange={(event) => setForm((current) => ({ ...current, confirmation: event.target.value }))}
                />
              </label>
              {status.message ? <p className={`account-security-status ${status.type}`}>{status.message}</p> : null}
              <footer>
                <button type="button" className="secondary-button" onClick={() => setOpen(false)}>Annuler</button>
                <button type="submit" className="primary-button" disabled={saving}>
                  {saving ? "Modification..." : "Modifier le mot de passe"}
                </button>
              </footer>
            </form>
          </section>
        </div>
      ) : null}
    </>
  );
}
