import React from "react";
import { Clock3 } from "lucide-react";

export default function GovernanceAuditTimeline({ events = [] }) {
  return (
    <article className="governance-panel audit-timeline">
      <header>
        <span>Trace des decisions</span>
        <strong>Qui a fait quoi, quand et pourquoi</strong>
      </header>
      <div className="timeline-list">
        {events.slice(0, 10).map((event) => (
          <div className="timeline-event" key={event.id}>
            <Clock3 size={15} />
            <div>
              <b>{event.eventType}</b>
              <span>{event.referenceId} | {event.family} | {event.actor}</span>
              <small>{event.justification}</small>
            </div>
            <time>{event.date}</time>
          </div>
        ))}
      </div>
    </article>
  );
}
