import React from "react";
import { FilterX, RefreshCcw } from "lucide-react";
import Skeleton from "../../../ui/Skeleton";
import WorkflowGuardEmptyState from "../../projects/WorkflowGuardEmptyState";
import ProjectWorkflowStepper from "../../projects/ProjectWorkflowStepper";
import ApprovisionnementKpiBand from "../components/ApprovisionnementKpiBand";
import CommandesPanel from "../components/CommandesPanel";
import FournisseursPanel from "../components/FournisseursPanel";
import RisquesApprovisionnement from "../components/RisquesApprovisionnement";
import LogistiquePanel from "../components/LogistiquePanel";
import LivraisonTimeline from "../components/LivraisonTimeline";
import ApprovisionnementCopilot from "../components/ApprovisionnementCopilot";
import { useApprovisionnementDashboard } from "../hooks/useApprovisionnementDashboard";

export default function ApprovisionnementDashboard() {
  const {
    data,
    error,
    isLoading,
    isFetching,
    refetch,
    project,
    workflow,
    activeChips,
    crossFiltering,
  } = useApprovisionnementDashboard();
  const setupDone = workflow.steps?.find((step) => step.id === "configuration")?.state === "done";
  const scenarioReady = workflow.scenario?.is_ready || workflow.steps?.find((step) => step.id === "scenarios")?.state === "done";
  const dashboard = data || {};

  const handleOrderSelect = (order) => {
    crossFiltering.applyDrilldown(
      { lot: order.lot, fournisseur: order.supplier },
      { source: "approvisionnement", title: order.reference, metric: order.status }
    );
  };

  const handleSupplierSelect = (supplier) => {
    crossFiltering.applyDrilldown(
      { fournisseur: supplier.name },
      { source: "approvisionnement-suppliers", title: supplier.name, metric: `${supplier.trustScore}/100` }
    );
  };

  return (
    <main className="appro-dashboard-page">
      <section className="appro-dashboard-hero">
        <div>
          <p className="eyebrow">Pilotage Approvisionnement</p>
          <h1>Commandes, fournisseurs, risques et logistique du projet actif</h1>
          <p>
            Couche d’orchestration SP2I au-dessus des arbitrages achat, du workflow projet,
            des simulations CAPEX et de l’exécution chantier.
          </p>
        </div>
        <div className="appro-hero-actions">
          <button type="button" onClick={() => refetch()}><RefreshCcw size={16} /> Actualiser</button>
          <button type="button" onClick={() => crossFiltering.reset()}><FilterX size={16} /> Réinitialiser</button>
        </div>
      </section>

      {error ? <div className="app-error">Pilotage approvisionnement indisponible : {error.message}</div> : null}
      {isFetching ? <div className="live-refresh">Synchronisation du cockpit approvisionnement...</div> : null}
      {isLoading ? <Skeleton /> : null}

      {!setupDone ? (
        <WorkflowGuardEmptyState
          title="Configuration projet requise"
          message="Ce projet doit être configuré avant de piloter l’approvisionnement."
          actionLabel="Configurer le projet"
          actionRoute="/app/projects"
          severity="blocking"
          currentStep={workflow.label}
          requiredStep="Configuration projet"
        />
      ) : null}
      {setupDone && !scenarioReady ? (
        <WorkflowGuardEmptyState
          title="Scénario CAPEX requis"
          message="Lancez une simulation avant de consolider le pilotage approvisionnement."
          actionLabel="Tester un scénario"
          actionRoute="/app/simulation"
          currentStep={workflow.steps?.find((step) => step.id === "scenarios")?.status}
          requiredStep="Simulation CAPEX"
        />
      ) : null}

      <section className="appro-product-map" aria-label="Responsabilités produit">
        <span><b>Synthèse</b> /app</span>
        <span><b>CAPEX</b> /app/simulation</span>
        <span><b>Opérations achat</b> /app/procurement</span>
        <span className="active"><b>Pilotage appro.</b> /app/approvisionnement</span>
        <span><b>Chantier</b> /app/site</span>
      </section>

      {activeChips.length ? (
        <section className="appro-filter-strip">
          {activeChips.map((chip) => <span key={`${chip.key}-${chip.value}`}>{chip.label} : {chip.value}</span>)}
        </section>
      ) : null}

      <ProjectWorkflowStepper workflow={workflow} compact />
      <ApprovisionnementKpiBand kpis={dashboard.kpis} />

      <section className="appro-dashboard-layout">
        <div className="appro-main-stack">
          <CommandesPanel orders={dashboard.orders || []} onSelect={handleOrderSelect} />
          <section className="appro-secondary-grid">
            <FournisseursPanel suppliers={dashboard.suppliers || []} onSupplier={handleSupplierSelect} />
            <LogistiquePanel logistics={dashboard.logistics || {}} />
          </section>
          <RisquesApprovisionnement risks={dashboard.risks || []} />
          <LivraisonTimeline timeline={dashboard.timeline || []} />
        </div>
        <ApprovisionnementCopilot
          project={project}
          workflow={workflow}
          recommendations={dashboard.recommendations || []}
          alerts={dashboard.alerts || []}
        />
      </section>
    </main>
  );
}
