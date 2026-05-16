import React from "react";

export default function AnalyticsCard({ title, eyebrow, children, action }) {
  return (
    <article className="panel-card">
      <header>
        <div>
          {eyebrow ? <span>{eyebrow}</span> : null}
          <h2>{title}</h2>
        </div>
        {action}
      </header>
      {children}
    </article>
  );
}
