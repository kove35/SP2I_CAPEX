import React from "react";
import ReactECharts from "echarts-for-react";

class ChartErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("BI CHART ERROR", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="chart-fallback" style={{ minHeight: this.props.height }}>
          Visualisation momentanement indisponible.
        </div>
      );
    }
    return this.props.children;
  }
}

export default function BIChart({ option, height = 280, onEvents, chartKey }) {
  const safeOption = React.useMemo(() => option || { series: [] }, [option]);

  return (
    <ChartErrorBoundary key={chartKey || "chart"} height={height}>
      <ReactECharts
        key={chartKey}
        option={safeOption}
        style={{ height, width: "100%" }}
        notMerge
        lazyUpdate={false}
        opts={{ renderer: "canvas" }}
        onEvents={onEvents}
      />
    </ChartErrorBoundary>
  );
}
