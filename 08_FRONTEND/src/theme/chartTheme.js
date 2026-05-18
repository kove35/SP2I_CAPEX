import { analyticsColors, chartPalette } from "./colors";

export const chartTheme = {
  color: chartPalette,
  textStyle: { color: analyticsColors.muted },
  grid: { left: 46, right: 22, top: 38, bottom: 38 },
  splitLine: { lineStyle: { color: "rgba(148,163,184,.12)" } },
  axisLabel: { color: analyticsColors.muted },
  tooltip: {
    backgroundColor: "rgba(7, 17, 31, .96)",
    borderColor: "rgba(148, 163, 184, .24)",
    textStyle: { color: analyticsColors.text },
  },
};
