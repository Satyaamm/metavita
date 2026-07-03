/**
 * Knowledge domain Zustand stores — server-data slices for sources, documents,
 * the document/chunk inspector, and indexes. Stores own loading/error status and
 * call the typed `api` transport; pages subscribe and render skeletons/empties.
 */
import { create } from "zustand";
import {
  type ChunkItem,
  type DataSource,
  type DocumentItem,
  type IndexItem,
  type Modality,
  type SourceType,
  api,
} from "../api";

export type AsyncStatus = "idle" | "loading" | "ready" | "error";

// --- Sources ---
interface SourcesState {
  items: DataSource[];
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
  create: (b: {
    name: string;
    type?: SourceType;
    modality?: Modality;
    connector?: string | null;
  }) => Promise<DataSource>;
  crawl: (b: { url: string; max_pages?: number; same_domain?: boolean; name?: string }) => Promise<{
    documents: number;
    chunks: number;
  }>;
  ingestVideo: (b: { url: string; name?: string }) => Promise<{ chunks: number }>;
}

export const useSourcesStore = create<SourcesState>((set, get) => ({
  items: [],
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listSources();
      set({ items: r.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (b) => {
    const s = await api.createSource(b);
    set((st) => ({ items: [s, ...st.items] }));
    return s;
  },
  crawl: async (b) => {
    const r = await api.crawl(b);
    const sources = await api.listSources();
    set({ items: sources.items });
    return { documents: r.documents, chunks: r.chunks };
  },
  ingestVideo: async (b) => {
    const r = await api.ingestVideo(b);
    const sources = await api.listSources();
    set({ items: sources.items });
    return { chunks: r.chunks };
  },
}));

// --- Documents (list, filtered) ---
interface DocumentsState {
  items: DocumentItem[];
  total: number;
  status: AsyncStatus;
  error?: string;
  fetch: (params?: {
    q?: string;
    source_id?: string;
    limit?: number;
    offset?: number;
  }) => Promise<void>;
}

export const useDocumentsStore = create<DocumentsState>((set) => ({
  items: [],
  total: 0,
  status: "loading",
  fetch: async (params = {}) => {
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listDocuments(params);
      set({ items: r.items, total: r.total, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
}));

// --- Document detail / chunk inspector ---
interface DocDetailState {
  doc: DocumentItem | null;
  chunks: ChunkItem[];
  status: AsyncStatus;
  error?: string;
  fetch: (id: string) => Promise<void>;
}

export const useDocDetailStore = create<DocDetailState>((set) => ({
  doc: null,
  chunks: [],
  status: "idle",
  fetch: async (id) => {
    set({ status: "loading", error: undefined, doc: null, chunks: [] });
    try {
      const r = await api.getDocumentChunks(id);
      set({ doc: r.document, chunks: r.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
}));

// --- Indexes ---
interface IndexesState {
  items: IndexItem[];
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
  create: (b: {
    name: string;
    modality?: Modality;
    embedding_provider?: string;
    embedding_model?: string;
    chunk_size?: number;
    overlap?: number;
  }) => Promise<IndexItem>;
}

export const useIndexesStore = create<IndexesState>((set, get) => ({
  items: [],
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listIndexes();
      set({ items: r.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (b) => {
    const i = await api.createIndex(b);
    set((st) => ({ items: [i, ...st.items] }));
    return i;
  },
}));
