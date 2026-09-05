import React from "react";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";

export default function KpiTrendBadge({ delta, positiveIsGood = true }) {
  if (delta === null || delta === undefined) return null;
  const value = Number(delta);
  const direction = value > 0 ? "up" : value < 0 ? "down" : "flat";
  const good = direction === "flat" || (positiveIsGood ? value >= 0 : value <= 0);
  const Icon = direction === "up" ? ArrowUpRight : direction === "down" ? ArrowDownRight : ArrowRight;

  return (
    <span className={`kpi-trend-badge ${good ? "good" : "watch"}`}>
      <Icon size={13} />
      {Math.abs(value).toFixed(1)}%
    </span>
  );
}
