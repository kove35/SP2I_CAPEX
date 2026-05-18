const FAMILY_ALIASES = {
  default: "Non classe metier",
  "": "Non classe metier",
  null: "Non classe metier",
  undefined: "Non classe metier",
  gros_oeuvre: "Gros oeuvre",
  electricite: "Electricite",
  plomberie: "Plomberie",
  climatisation: "CVC",
  menuiserie: "Menuiserie",
  peinture: "Peinture",
  ascenseur: "Ascenseur",
};

export function toBusinessLabel(value, fallback = "Non renseigne") {
  const raw = String(value ?? "").trim();
  if (!raw || raw.toLowerCase() === "default") return fallback;
  return FAMILY_ALIASES[raw] || FAMILY_ALIASES[raw.toLowerCase()] || raw;
}

export function compactLabel(value, size = 24) {
  const label = toBusinessLabel(value);
  return label.length > size ? `${label.slice(0, Math.max(size - 1, 1))}...` : label;
}

export function normalizeFamily(value) {
  return toBusinessLabel(value, "Non classe metier");
}

export function normalizeDecision(value) {
  const decision = String(value || "").toUpperCase();
  return decision === "IMPORT" ? "IMPORT" : "LOCAL";
}
