export function formatMoney(value) {
  return `${Number(value || 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 })} FCFA`;
}

export function formatCurrency(value, currency = "FCFA") {
  const code = currency || "FCFA";
  const suffix = code === "USD" ? "USD" : code === "EUR" ? "EUR" : "FCFA";
  return `${Number(value || 0).toLocaleString("fr-FR", { maximumFractionDigits: code === "FCFA" ? 0 : 2 })} ${suffix}`;
}

export function formatPercent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

export function average(rows, key) {
  if (!rows?.length) return 0;
  return rows.reduce((sum, row) => sum + Number(row[key] || 0), 0) / rows.length;
}
