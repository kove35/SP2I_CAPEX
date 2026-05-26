import React from "react";

const EVENT_LABELS = {
  WORKFLOW_BLOCKED: "Workflow bloqué",
  LOT_AT_RISK: "Lot à risque",
  ETA_RISK: "ETA à surveiller",
};

export default function SpatialEventFeed({ summary }) {
  const events = summary?.event_feed || [];

  if (!events.length) return null;

  return (
    <section className="spatial-panel spatial-event-feed" data-testid="spatial-event-feed">
      <div className="spatial-panel-header">
        <div>
          <p className="eyebrow">Event engine</p>
          <h3>Événements chantier spatiaux</h3>
        </div>
      </div>

      <div className="spatial-event-list">
        {events.slice(0, 6).map((event, index) => (
          <article key={`${event.event_type}-${event.entity_id || index}`} className={`spatial-event-item ${event.severity || "info"}`}>
            <span>{EVENT_LABELS[event.event_type] || event.event_type || "Événement"}</span>
            <strong>{event.zone || "Zone non renseignée"}</strong>
            <p>{event.message}</p>
            {event.recommended_action ? <small>{event.recommended_action}</small> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
