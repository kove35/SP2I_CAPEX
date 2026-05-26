import React from "react";
import SpatialCriticalPathPanel from "./SpatialCriticalPathPanel";
import SpatialDependencyPanel from "./SpatialDependencyPanel";
import SpatialExecutionBoard from "./SpatialExecutionBoard";
import SpatialEventFeed from "./SpatialEventFeed";
import SpatialExecutiveKpis from "./SpatialExecutiveKpis";
import SpatialHeatmapPanel from "./SpatialHeatmapPanel";
import SpatialPlanningBoard from "./SpatialPlanningBoard";
import SpatialRiskPropagationPanel from "./SpatialRiskPropagationPanel";
import SpatialStoragePanel from "./SpatialStoragePanel";
import SpatialTimelineBoard from "./SpatialTimelineBoard";

export default function SpatialWorkflowPanel({ summary, filters }) {
  return (
    <>
      <SpatialExecutiveKpis summary={summary} />
      <section className="spatial-workflow-grid">
        <SpatialTimelineBoard summary={summary} filters={filters} />
        <SpatialEventFeed summary={summary} />
        <SpatialExecutionBoard summary={summary} filters={filters} />
        <SpatialHeatmapPanel summary={summary} filters={filters} />
        <SpatialDependencyPanel summary={summary} />
        <SpatialStoragePanel summary={summary} filters={filters} />
        <SpatialPlanningBoard summary={summary} />
        <SpatialCriticalPathPanel summary={summary} />
        <SpatialRiskPropagationPanel summary={summary} />
      </section>
    </>
  );
}
