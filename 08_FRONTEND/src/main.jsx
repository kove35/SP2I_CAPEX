import React from "react";
import { createRoot } from "react-dom/client";
import QueryProvider from "./app/QueryProvider";
import AppRouter from "./routes/AppRouter";
import { AppStoreProvider } from "./store/appStore.jsx";
import "./styles.css";

createRoot(document.getElementById("root")).render(
  <QueryProvider>
    <AppStoreProvider>
      <AppRouter />
    </AppStoreProvider>
  </QueryProvider>
);
