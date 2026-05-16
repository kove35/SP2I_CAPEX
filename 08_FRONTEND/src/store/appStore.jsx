import React from "react";

const AppStoreContext = React.createContext(null);

export function AppStoreProvider({ children }) {
  const [state, setState] = React.useState({
    activeProject: "Pointe-Noire CAPEX",
    activeScenario: "FRONT_COCKPIT_TEST",
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
        activeProject: "Pointe-Noire CAPEX",
        activeScenario: "FRONT_COCKPIT_TEST",
        lastSimulation: null,
      },
      setState: () => {},
    };
  }
  return context;
}
