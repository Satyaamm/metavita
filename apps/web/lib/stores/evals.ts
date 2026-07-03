/** Evals Zustand store — datasets list + create. */
import { create } from "zustand";
import { type EvalDatasetItem, type EvalQA, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface EvalsState {
  items: EvalDatasetItem[];
  status: AsyncStatus;
  fetch: () => Promise<void>;
  create: (name: string, items: EvalQA[]) => Promise<EvalDatasetItem>;
}

export const useEvalsStore = create<EvalsState>((set) => ({
  items: [],
  status: "loading",
  fetch: async () => {
    set({ status: "loading" });
    try {
      const r = await api.listDatasets();
      set({ items: r.items, status: "ready" });
    } catch {
      set({ status: "error" });
    }
  },
  create: async (name, items) => {
    const d = await api.createDataset({ name, items });
    set((s) => ({ items: [d, ...s.items] }));
    return d;
  },
}));

/** Parse a textarea into Q/A items: one per line, optional "question | expected". */
export function parseQuestions(text: string): EvalQA[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [q, ...rest] = line.split("|");
      const expected = rest.join("|").trim();
      return { question: q.trim(), expected: expected || null };
    });
}
