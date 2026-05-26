export function buildSpatialOptions(summary = {}) {
  const rows = summary.capex_by_batiment || [];
  const tree = summary.hierarchy || [];
  const batiments = rows.map((item) => item.label).filter(Boolean);
  const niveaux = new Set();
  const pieces = new Set();
  const apparts = new Set();

  function walk(nodes = []) {
    nodes.forEach((node) => {
      if (node.level === "niveau") niveaux.add(node.label);
      if (node.level === "piece") pieces.add(node.label);
      if (node.level === "appart") apparts.add(node.label);
      walk(node.children || []);
    });
  }

  walk(tree);
  return {
    batiments,
    niveaux: Array.from(niveaux),
    apparts: Array.from(apparts),
    pieces: Array.from(pieces),
  };
}

export function filterSpatialRows(rows = [], filters = {}) {
  return rows.filter((row) => {
    if (filters.batiment && row.batiment && row.batiment !== filters.batiment && row.label !== filters.batiment) return false;
    if (filters.niveau && row.niveau && row.niveau !== filters.niveau && row.label !== filters.niveau) return false;
    if (filters.appart && row.appart && row.appart !== filters.appart && row.label !== filters.appart) return false;
    if (filters.piece && row.piece && row.piece !== filters.piece && row.label !== filters.piece) return false;
    return true;
  });
}

export function getNextSpatialFocus(summary = {}) {
  const risks = summary.risk_heatmap || [];
  const highRisk = [...risks].sort((a, b) => Number(b.risk_score || 0) - Number(a.risk_score || 0))[0];
  if (highRisk?.risk_score > 0) {
    return {
      label: [highRisk.batiment, highRisk.niveau, highRisk.piece].filter(Boolean).join(" › "),
      message: `${highRisk.at_risk_count || 0} action(s) à risque, ${highRisk.blocked_count || 0} blocage(s).`,
    };
  }
  const topCapex = (summary.capex_by_batiment || [])[0];
  if (topCapex) {
    return {
      label: topCapex.label,
      message: "Zone CAPEX principale à suivre dans le pilotage chantier.",
    };
  }
  return null;
}
