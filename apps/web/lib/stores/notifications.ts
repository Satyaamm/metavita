/** Notifications store — the header bell's inbox (its own store, not the audit log). */
import { create } from "zustand";
import { type NotificationItem, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface NotificationsState {
  items: NotificationItem[];
  unread: number;
  status: AsyncStatus;
  fetch: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
  dismiss: (id: string) => Promise<void>;
  clearAll: () => Promise<void>;
}

export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  items: [],
  unread: 0,
  status: "idle",
  fetch: async () => {
    // Safe to call on an interval — never throws into the poller.
    try {
      const r = await api.listNotifications(20);
      set({ items: r.items, unread: r.unread, status: "ready" });
    } catch {
      set({ status: "error" });
    }
  },
  markRead: async (id) => {
    const target = get().items.find((i) => i.id === id);
    if (!target || target.read) return;
    set((s) => ({
      items: s.items.map((i) => (i.id === id ? { ...i, read: true } : i)),
      unread: Math.max(0, s.unread - 1),
    }));
    try {
      await api.markNotificationRead(id);
    } catch {
      /* next poll reconciles */
    }
  },
  markAllRead: async () => {
    if (get().unread === 0) return;
    set((s) => ({ items: s.items.map((i) => ({ ...i, read: true })), unread: 0 }));
    try {
      await api.markAllNotificationsRead();
    } catch {
      /* next poll reconciles */
    }
  },
  dismiss: async (id) => {
    const wasUnread = !get().items.find((i) => i.id === id)?.read;
    set((s) => ({
      items: s.items.filter((i) => i.id !== id),
      unread: wasUnread ? Math.max(0, s.unread - 1) : s.unread,
    }));
    try {
      await api.dismissNotification(id);
    } catch {
      /* next poll reconciles */
    }
  },
  clearAll: async () => {
    set({ items: [], unread: 0 });
    try {
      await api.clearNotifications();
    } catch {
      /* next poll reconciles */
    }
  },
}));
