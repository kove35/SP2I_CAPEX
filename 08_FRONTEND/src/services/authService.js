import { request } from "./apiClient";

const SESSION_KEY = "sp2i_session";

export function getStoredSession() {
  try {
    return JSON.parse(window.localStorage.getItem(SESSION_KEY) || "null");
  } catch {
    return null;
  }
}

export function storeSession(session) {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

export function clearSession() {
  window.localStorage.removeItem(SESSION_KEY);
}

export async function loginUser(payload) {
  const session = await request({ url: "/auth/login", method: "POST", data: payload });
  return storeSession(session);
}

export async function registerUser(payload) {
  const session = await request({ url: "/auth/register", method: "POST", data: payload });
  return storeSession(session);
}

export function createDemoSession() {
  return storeSession({
    access_token: "demo-session",
    token_type: "demo",
    user: {
      id: 0,
      email: "demo@sp2i.local",
      full_name: "Utilisateur demonstration",
      role: "MANAGER",
      is_active: true,
    },
  });
}
