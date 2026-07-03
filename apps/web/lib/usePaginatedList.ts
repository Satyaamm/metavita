/**
 * Centralized list controller — pagination + filters + URL sync + fetch effect.
 *
 * Keeps page/size/filters in the URL (so views are bookmarkable/shareable), and
 * re-fetches whenever any of them change. Pages provide a stable `fetch` (a Zustand
 * store action) and the current `filters`; the hook builds `{limit, offset, …filters}`
 * and returns the page state + URL writers. Pair with `<ListView>` for the
 * loading/skeleton/empty/error side-effects.
 */
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { DEFAULT_PAGE_SIZE, offsetFor } from "./pagination";

type FetchArgs<F> = { limit: number; offset: number } & F;

interface Options<F extends Record<string, unknown>> {
  basePath: string; // e.g. "/traces"
  fetch: (args: FetchArgs<F>) => unknown; // stable store action
  filters?: F; // current filter values (already read from the URL by the caller)
}

export interface PaginatedListController {
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  /** Update any URL params (filters); resets to page 1 unless `page` is given. */
  setParams: (next: Record<string, string | number | undefined>) => void;
}

export function usePaginatedList<F extends Record<string, unknown>>({
  basePath,
  fetch,
  filters,
}: Options<F>): PaginatedListController {
  const router = useRouter();
  const params = useSearchParams();
  const page = Math.max(1, Number(params.get("page") ?? 1));
  const pageSize = Number(params.get("size") ?? DEFAULT_PAGE_SIZE);
  const filterKey = JSON.stringify(filters ?? {});

  // Re-fetch on page/size/filter change. `fetch` is a stable store action;
  // `filterKey` collapses the filter object to a primitive dep.
  // biome-ignore lint/correctness/useExhaustiveDependencies: filterKey stands in for filters
  useEffect(() => {
    fetch({ limit: pageSize, offset: offsetFor(page, pageSize), ...(filters ?? ({} as F)) });
  }, [page, pageSize, filterKey, fetch]);

  function setParams(next: Record<string, string | number | undefined>) {
    const sp = new URLSearchParams(params.toString());
    // A filter change (anything other than an explicit page) returns to page 1.
    if (!("page" in next)) sp.set("page", "1");
    for (const [k, v] of Object.entries(next)) {
      if (v === undefined || v === "") sp.delete(k);
      else sp.set(k, String(v));
    }
    router.replace(`${basePath}${sp.toString() ? `?${sp}` : ""}`);
  }

  return {
    page,
    pageSize,
    setPage: (p) => setParams({ page: p }),
    setPageSize: (s) => setParams({ size: s, page: 1 }),
    setParams,
  };
}
