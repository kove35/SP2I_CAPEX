import React from "react";
import { PROJECT_CONTEXT, SCENARIO_OPTIONS } from "../utils/businessContext";

const APP_STATE_KEY = "sp2i:appState";

function readPersistedState() {
  if (typeof window === "undefined") return null;
  try {
    const stored = window.localStorage.getItem(APP_STATE_KEY);
    if (!stored) return null;
    const parsed = JSON.parse(stored);
    return typeof parsed === "object" && parsed ? parsed : null;
  } catch {
    return null;
  }
}

const defaultState = {
  activeProject: PROJECT_CONTEXT.code,
  activeProjectDetails: null,
  activeScenario: SCENARIO_OPTIONS[0].code,
  lastSimulation: null,
  lastSimulationProject: null,
};

const AppStoreContext = React.createContext(null);

export function AppStoreProvider({ children }) {
  const [state, setState] = React.useState(() => {
    const persisted = readPersistedState();
    return persisted ? { ...defaultState, ...persisted } : defaultState;
  });

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(APP_STATE_KEY, JSON.stringify(state));
    } catch {
      // Ignore storage failures in demo mode.
    }
  }, [state]);

  const value = React.useMemo(() => ({ state, setState }), [state]);
  return <AppStoreContext.Provider value={value}>{children}</AppStoreContext.Provider>;
}

export function useAppStore() {
  const context = React.useContext(AppStoreContext);
  if (!context) {
    return {
      state: {
        activeProject: PROJECT_CONTEXT.code,
        activeProjectDetails: null,
        activeScenario: SCENARIO_OPTIONS[0].code,
        lastSimulation: null,
        lastSimulationProject: null,
      },
      setState: () => {},
    };
  }
  return context;
}
