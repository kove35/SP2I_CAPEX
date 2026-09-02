import React from "react";
import { ArrowRight, LockKeyhole, UserPlus } from "lucide-react";
import { loginUser, registerUser } from "../services/authService";

export default function LoginCard({ onAuthenticated, onDiscover }) {
  const [mode, setMode] = React.useState("login");
  const [form, setForm] = React.useState({ email: "", password: "", full_name: "" });
  const [status, setStatus] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setStatus("");
    try {
      const payload = { email: form.email, password: form.password };
      const session = mode === "register"
        ? await registerUser({ ...payload, full_name: form.full_name })
        : await loginUser(payload);
      onAuthenticated(session);
    } catch (error) {
      setStatus(error.message || "Connexion indisponible. Utilisez l'acces demonstration.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="landing-login-card" onSubmit={submit}>
      <div className="login-card-heading">
        <span><LockKeyhole size={16} /> Workspace securise</span>
        <h2>Espace Projet SP2I</h2>
        <p>Connectez votre organisation, choisissez un projet, puis pilotez DQE, scenarios, analytics et gouvernance.</p>
      </div>

      {mode === "register" ? (
        <label>
          Nom complet
          <input name="full_name" value={form.full_name} onChange={updateField} placeholder="Awa Moukala" autoComplete="name" />
        </label>
      ) : null}

      <label>
        Email
        <input name="email" value={form.email} onChange={updateField} placeholder="vous@organisation.com" type="email" autoComplete="email" required />
      </label>

      <label>
        Mot de passe
        <input name="password" value={form.password} onChange={updateField} placeholder="Minimum 12 caracteres" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required />
      </label>

      {status ? <p className="login-card-status">{status}</p> : null}

      <div className="login-card-actions">
        <button type="submit" disabled={loading}>
          {mode === "login" ? "Se connecter" : "Creer un compte"} <ArrowRight size={16} />
        </button>
        <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          <UserPlus size={16} /> {mode === "login" ? "Creer un compte" : "J'ai deja un compte"}
        </button>
      </div>

      <div className="login-card-links">
        <button type="button">Mot de passe oublie</button>
        <button type="button" onClick={onDiscover}>Decouvrir SP2I</button>
      </div>

      <div className="workspace-chain" aria-label="Structure plateforme SP2I">
        <span>Organisation</span>
        <i />
        <span>Utilisateurs</span>
        <i />
        <span>Projets</span>
        <i />
        <span>Governance</span>
      </div>
    </form>
  );
}
