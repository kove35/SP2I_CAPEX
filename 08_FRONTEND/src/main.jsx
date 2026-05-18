import React from "react";
import { createRoot } from "react-dom/client";
import QueryProvider from "./app/QueryProvider";
import AppRouter from "./routes/AppRouter";
import { AppStoreProvider } from "./store/appStore.jsx";
import "./styles.css";

window.__SP2I_ERRORS__ = [];
window.addEventListener("error", (event) => {
  window.__SP2I_ERRORS__.push({
    type: "error",
    message: event.message,
    source: event.filename,
    line: event.lineno,
    column: event.colno,
  });
});
window.addEventListener("unhandledrejection", (event) => {
  window.__SP2I_ERRORS__.push({
    type: "unhandledrejection",
    message: String(event.reason?.message || event.reason || "Unhandled promise rejection"),
  });
});

class RootErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("SP2I ROOT ERROR", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="root-error-shell">
          <section>
            <p className="eyebrow">SP2I runtime guard</p>
            <h1>Le cockpit a detecte une erreur d'affichage.</h1>
            <p>{this.state.error.message || "Erreur JavaScript non identifiee."}</p>
            <button type="button" onClick={() => window.location.reload()}>
              Recharger SP2I
            </button>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById("root")).render(
  <RootErrorBoundary>
    <QueryProvider>
      <AppStoreProvider>
        <AppRouter />
      </AppStoreProvider>
    </QueryProvider>
  </RootErrorBoundary>
);
