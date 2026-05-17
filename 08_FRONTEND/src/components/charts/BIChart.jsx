import React from "react";
import ReactECharts from "echarts-for-react";

export default function BIChart({ option, height = 280, onEvents }) {
  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      notMerge
      lazyUpdate
      opts={{ renderer: "canvas" }}
      onEvents={onEvents}
    />
  );
}
