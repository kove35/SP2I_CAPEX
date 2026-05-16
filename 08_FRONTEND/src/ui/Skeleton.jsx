import React from "react";

export default function Skeleton({ rows = 3 }) {
  return (
    <div className="skeleton-stack">
      {Array.from({ length: rows }).map((_, index) => (
        <i key={index} />
      ))}
    </div>
  );
}
