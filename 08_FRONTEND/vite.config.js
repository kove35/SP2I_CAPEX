import { defineConfig } from "vite";

// Decoupage des dependances lourdes en chunks vendors dedies.
// React/react-dom/scheduler restent dans un chunk unique (une seule instance partagee).
const VENDOR_CHUNKS = [
  { match: /node_modules[\\/]ag-grid/, name: "vendor-ag-grid" },
  { match: /node_modules[\\/](echarts|zrender)/, name: "vendor-echarts" },
  { match: /node_modules[\\/](react-dom|react|scheduler)[\\/]/, name: "vendor-react" },
  { match: /node_modules[\\/]@tanstack/, name: "vendor-query" },
  { match: /node_modules[\\/]axios/, name: "vendor-axios" },
  { match: /node_modules[\\/]lucide-react/, name: "vendor-icons" },
  { match: /node_modules[\\/](antd|@ant-design|rc-[a-z0-9-]+|dayjs)/, name: "vendor-antd" },
];

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }
          for (const { match, name } of VENDOR_CHUNKS) {
            if (match.test(id)) {
              return name;
            }
          }
          return "vendor";
        },
      },
    },
  },
});
