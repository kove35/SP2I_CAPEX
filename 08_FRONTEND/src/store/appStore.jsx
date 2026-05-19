import React from "react";
import { PROJECT_CONTEXT, SCENARIO_OPTIONS } from "../utils/businessContext";

const AppStoreContext = React.createContext(null);

export function AppStoreProvider({ children }) {
  const [state, setState] = React.useState({
    activeProject: PROJECT_CONTEXT.code,
    activeScenario: SCENARIO_OPTIONS[0].code,
    lastSimulation: null,
  });

  const value = React.useMemo(() => ({ state, setState }), [state]);
  return <AppStoreContext.Provider value={value}>{children}</AppStoreContext.Provider>;
}

export function useAppStore() {
  const context = React.useContext(AppStoreContext);
  if (!context) {
    return {
      state: {
        activeProject: PROJECT_CONTEXT.code,
        activeScenario: SCENARIO_OPTIONS[0].code,
        lastSimulation: null,
      },
      setState: () => {},
    };
  }
  return context;
}
