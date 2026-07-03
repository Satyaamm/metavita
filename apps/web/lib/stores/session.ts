/** Session store — the signed-in account (from /auth/me) + JWT lifecycle. */
import { create } from "zustand";
import { type SessionMe, type SessionPayload, api, clearToken, setToken } from "../api";
import type { AsyncStatus } from "./knowledge";

interface SessionState {
  me: SessionMe | null;
  status: AsyncStatus;
  fetch: () => Promise<void>;
  /** Persist a login/signup/accept result and load the account. */
  setSession: (payload: SessionPayload) => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  me: null,
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading" });
    try {
      set({ me: await api.getMe(), status: "ready" });
    } catch {
      // 401 / no session — fall back gracefully.
      set({ me: null, status: "ready" });
    }
  },
  setSession: (payload) => {
    setToken(payload.token);
    set({ me: { user: payload.user, workspace: payload.workspace }, status: "ready" });
  },
}));

/** Clear the session and return to the sign-in page. */
export function signOut() {
  clearToken();
  useSessionStore.setState({ me: null, status: "ready" });
  window.location.href = "/login";
}
