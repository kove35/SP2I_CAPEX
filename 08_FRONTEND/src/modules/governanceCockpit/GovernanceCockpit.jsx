import React from "react";
import { FilterX, RefreshCcw, ShieldAlert } from "lucide-react";
import Skeleton from "../../ui/Skeleton";
import { useGovernanceCockpit } from "../../hooks/useGovernanceCockpit";
import { useGovernanceCockpitStore } from "../../stores/governanceCockpitStore";
import GovernanceAuditTimeline from "../../components/governanceCockpit/GovernanceAuditTimeline";
import GovernanceConfidenceMatrix from "../../components/governanceCockpit/GovernanceConfidenceMatrix";
import GovernanceDriftHeatmap from "../../components/governanceCockpit/GovernanceDriftHeatmap";
import GovernanceEscalationPanel from "../../components/governanceCockpit/GovernanceEscalationPanel";
import GovernanceExplainabilityPanel from "../../components/governanceCockpit/GovernanceExplainabilityPanel";
import GovernanceFamilyStatusBoard from "../../components/governanceCockpit/GovernanceFamilyStatusBoard";
import GovernanceKpiStrip from "../../components/governanceCockpit/GovernanceKpiStrip";
import GovernanceReviewQueue from "../../components/governanceCockpit/GovernanceReviewQueue";

export default function GovernanceCockpit() {
  const { data, references, selectedReference, isLoading, isFetching, error, refetch } = useGovernanceCockpit();
  const setSelectedReferenceId = useGovernanceCockpitStore((state) => state.setSelectedReferenceId);
  const setFilter = useGovernanceCockpitStore((state) => state.setFilter);
  const resetFilters = useGovernanceCockpitStore((state) => state.resetFilters);
  const filters = useGovernanceCockpitStore((state) => state.filters);

  const activeFilters = Object.entries(filters).filter(([, value]) => value);

  if (isLoading) {
    return (
      <main className="governance-cockpit-page">
        <Skeleton height={180} />
        <Skeleton height={520} />
      </main>
    );
  }

  return (
    <main className="governance-cockpit-page">
      <section className="governance-hero">
        <div>
          <p className="eyebrow"><ShieldAlert size={15} /> Gouvernance Enterprise</p>
          <h1>Governance Cockpit</h1>
          <p>Supervision humaine des risques procurement/CAPEX, escalations, blocages et validations explicables.</p>
        </div>
        <div className="governance-hero-actions">
          <button type="button" onClick={() => refetch()}><RefreshCcw size={15} /> Actualiser</button>
          <button type="button" onClick={resetFilters}><FilterX size={15} /> Reinitialiser</button>
        </div>
      </section>

      {error ? <div className="governance-error">Dataset API indisponible, fallback governance V1 actif.</div> : null}
      {isFetching ? <div className="live-refresh">Synchronisation governance...</div> : null}

      <GovernanceKpiStrip kpis={data?.kpis} />

      {activeFilters.length ? (
        <section className="governance-filter-strip">
          {activeFilters.map(([key, value]) => (
            <button type="button" key={key} onClick={() => setFilter(key, "")}>{key}: {value}</button>
          ))}
        </section>
      ) : null}

      <GovernanceFamilyStatusBoard families={data?.familyKpis || []} onSelect={(family) => setFilter("family", family)} />

      <section className="governance-main-grid">
        <GovernanceReviewQueue rows={references} onSelect={(row) => setSelectedReferenceId(row.referenceId)} />
        <div className="governance-side-stack">
          <GovernanceEscalationPanel escalations={data?.escalations || []} onSelect={(level) => setFilter("escalation", level)} />
          <GovernanceExplainabilityPanel reference={selectedReference} />
        </div>
      </section>

      <section className="governance-analytics-grid">
        <GovernanceDriftHeatmap rows={references} />
        <GovernanceConfidenceMatrix rows={references} />
      </section>

      <GovernanceAuditTimeline events={data?.auditTimeline || []} />
    </main>
  );
}
