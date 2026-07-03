/** Pure pagination helpers — used by the shared Pagination component and list pages. */

export const PAGE_SIZES = [10, 20, 50, 100] as const;
export const DEFAULT_PAGE_SIZE = 20;

export function pageCount(total: number, pageSize: number): number {
  return Math.max(1, Math.ceil(total / Math.max(1, pageSize)));
}

export function clampPage(page: number, total: number, pageSize: number): number {
  return Math.min(Math.max(1, page), pageCount(total, pageSize));
}

export function offsetFor(page: number, pageSize: number): number {
  return (Math.max(1, page) - 1) * pageSize;
}

/** The 1-based item range shown on a page, e.g. {from: 21, to: 40}. */
export function itemRange(
  page: number,
  pageSize: number,
  total: number,
): { from: number; to: number } {
  if (total === 0) return { from: 0, to: 0 };
  const from = offsetFor(page, pageSize) + 1;
  return { from, to: Math.min(from + pageSize - 1, total) };
}

/** Page numbers to render around the current page (clamped), within `span`. */
export function pageWindow(page: number, totalPages: number, span = 2): number[] {
  const start = Math.max(1, page - span);
  const end = Math.min(totalPages, page + span);
  const out: number[] = [];
  for (let p = start; p <= end; p++) out.push(p);
  return out;
}
