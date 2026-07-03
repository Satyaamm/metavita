/** Settings stores — workspace, members, provider credentials. */
import { create } from "zustand";
import { type CredentialItem, type MemberItem, type WorkspaceInfo, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface WorkspaceState {
  workspace: WorkspaceInfo | null;
  status: AsyncStatus;
  fetch: () => Promise<void>;
  save: (body: { name?: string; key_policy?: string; settings?: Record<string, unknown> }) => Promise<void>;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspace: null,
  status: "loading",
  fetch: async () => {
    set({ status: "loading" });
    try {
      set({ workspace: await api.getWorkspace(), status: "ready" });
    } catch {
      set({ status: "error" });
    }
  },
  save: async (body) => {
    const w = await api.updateWorkspace(body);
    set({ workspace: w });
  },
}));

interface MembersState {
  items: MemberItem[];
  status: AsyncStatus;
  fetch: () => Promise<void>;
  add: (email: string, role: string) => Promise<void>;
  remove: (id: string) => Promise<void>;
}

export const useMembersStore = create<MembersState>((set, get) => ({
  items: [],
  status: "loading",
  fetch: async () => {
    set({ status: "loading" });
    try {
      const r = await api.listMembers();
      set({ items: r.items, status: "ready" });
    } catch {
      set({ status: "error" });
    }
  },
  add: async (email, role) => {
    const m = await api.addMember({ email, role });
    set((s) => ({ items: [...s.items, m] }));
  },
  remove: async (id) => {
    await api.removeMember(id);
    set((s) => ({ items: s.items.filter((m) => m.membership_id !== id) }));
  },
}));

interface CredentialsState {
  items: CredentialItem[];
  status: AsyncStatus;
  fetch: () => Promise<void>;
  add: (body: { provider: string; label: string; key: string }) => Promise<void>;
  remove: (id: string) => Promise<void>;
}

export const useCredentialsStore = create<CredentialsState>((set) => ({
  items: [],
  status: "loading",
  fetch: async () => {
    set({ status: "loading" });
    try {
      const r = await api.listCredentials();
      set({ items: r.items, status: "ready" });
    } catch {
      set({ status: "error" });
    }
  },
  add: async (body) => {
    const c = await api.createCredential(body);
    set((s) => ({ items: [c, ...s.items] }));
  },
  remove: async (id) => {
    await api.deleteCredential(id);
    set((s) => ({ items: s.items.filter((c) => c.id !== id) }));
  },
}));
