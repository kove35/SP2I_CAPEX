const FAMILY_ALIASES = {
  default: "Classification en attente",
  unknown: "Classification en attente",
  "non classe": "Classification en attente",
  "non classé": "Classification en attente",
  "": "Classification en attente",
  null: "Classification en attente",
  undefined: "Classification en attente",
  gros_oeuvre: "Gros oeuvre",
  grosoeuvre: "Gros oeuvre",
  structure: "Structure",
  beton: "Structure",
  "béton": "Structure",
  electricite: "Electricite",
  "électricité": "Electricite",
  elec: "Electricite",
  plomberie: "Plomberie",
  climatisation: "CVC",
  cvc: "CVC",
  facade: "Facade",
  "façade": "Facade",
  alucobond: "Facade",
  revetement: "Revetement",
  "revêtement": "Revetement",
  revetements: "Revetement",
  "revêtements": "Revetement",
  menuiserie: "Menuiserie",
  menuiserie_aluminium: "Menuiserie aluminium",
  aluminium: "Menuiserie aluminium",
  bois: "Menuiserie bois",
  ferronnerie: "Metallerie",
  metallique: "Metallerie",
  "métallique": "Metallerie",
  peinture: "Peinture",
  ascenseur: "Ascenseur",
  securite: "Securite",
  "sécurité": "Securite",
  incendie: "Securite incendie",
};

export function toBusinessLabel(value, fallback = "Non renseigne") {
  const raw = String(value ?? "").trim();
  if (!raw || ["default", "unknown", "non classe", "non classé"].includes(raw.toLowerCase())) return fallback;
  return FAMILY_ALIASES[raw] || FAMILY_ALIASES[raw.toLowerCase()] || raw;
}

export function compactLabel(value, size = 24) {
  const label = toBusinessLabel(value);
  return label.length > size ? `${label.slice(0, Math.max(size - 1, 1))}...` : label;
}

export function normalizeFamily(value) {
  return toBusinessLabel(value, "Classification en attente");
}

export function normalizeDecision(value) {
  const decision = String(value || "").toUpperCase();
  return decision === "IMPORT" ? "IMPORT" : "LOCAL";
}
