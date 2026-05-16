import React from "react";

export default function RiskCard({ title, level = "MEDIUM", score, text }) {
  return (
    <article className={`analytics-card risk-card risk-${String(level).toLowerCase()}`}>
      <div>
        <span>{title}</span>
        <strong>{level}</strong>
      </div>
      {score !== undefined ? <p>{score}</p> : null}
      {text ? <small>{text}</small> : null}
    </article>
  );
}
