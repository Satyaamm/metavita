/**
 * App/UI Zustand store — global client state that isn't server data:
 * feature flags (seeded from registry defaults), sidebar, and other UI toggles.
 */
import { create } from "zustand";
import { FLAG_DEFAULTS, type FlagKey } from "../featureFlags";

interface UIState {
  flags: Record<FlagKey, boolean>;
  setFlag: (key: FlagKey, value: boolean) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  flags: { ...FLAG_DEFAULTS },
  setFlag: (key, value) => set((s) => ({ flags: { ...s.flags, [key]: value } })),
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));

/** Convenience selector hook for a single flag. */
export const useFlag = (key: FlagKey): boolean => useUIStore((s) => s.flags[key]);
