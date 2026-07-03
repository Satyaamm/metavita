"use client";

import {
  Caption1,
  SearchBox,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  makeStyles,
} from "@fluentui/react-components";
import { DocumentMultipleRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { ListView } from "@/components/ListView";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { TableSkeleton } from "@/components/Skeletons";
import { StatusBadge } from "@/components/StatusBadge";
import { useDocumentsStore } from "@/lib/stores/knowledge";
import { usePaginatedList } from "@/lib/usePaginatedList";
import { appTokens, palette } from "../../theme";

const useStyles = makeStyles({
  toolbar: { display: "flex", gap: "12px", alignItems: "center" },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    overflow: "hidden",
  },
  link: { color: palette.brandPrimary, textDecoration: "none", fontWeight: 600 },
});

function fmt(dt: string | null) {
  return dt ? new Date(dt).toLocaleString() : "";
}

function DocumentsInner() {
  const styles = useStyles();
  const params = useSearchParams();
  const q = params.get("q") ?? "";
  const sourceId = params.get("source_id") ?? undefined;

  const [term, setTerm] = useState(q);
  const { items, total, status, error, fetch } = useDocumentsStore();
  const { page, pageSize, setPage, setPageSize, setParams } = usePaginatedList({
    basePath: "/knowledge/documents",
    fetch,
    filters: { q: q || undefined, source_id: sourceId },
  });

  return (
    <>
      <PageHeader
        title="Documents"
        description="Every ingested document and its indexing status. Open one to inspect how it was chunked."
      />

      <div className={styles.toolbar}>
        <SearchBox
          value={term}
          onChange={(_, d) => setTerm(d.value)}
          onKeyDown={(e) => e.key === "Enter" && setParams({ q: term })}
          dismiss={{ onClick: () => setParams({ q: undefined }) }}
          placeholder="Search by filename…"
          style={{ width: 320 }}
        />
        {sourceId && <Caption1 style={{ color: palette.inkSubtle }}>filtered by source</Caption1>}
      </div>

      <ListView
        status={status}
        error={error}
        isEmpty={items.length === 0}
        skeleton={<TableSkeleton rows={6} />}
        empty={
          <EmptyState
            icon={<DocumentMultipleRegular />}
            title={q ? "No matching documents" : "No documents indexed"}
            description={
              q
                ? "Try a different search term."
                : "Add a data source to ingest documents — they'll appear here with a chunk inspector."
            }
            actionLabel={q ? undefined : "Add a source"}
            actionHref={q ? undefined : "/knowledge/sources/new"}
          />
        }
        footer={
          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
        }
      >
        <div className={styles.card}>
          <Table aria-label="Documents">
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Filename</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Added</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((d) => (
                <TableRow key={d.id}>
                  <TableCell>
                    <Link href={`/knowledge/documents/${d.id}`} className={styles.link}>
                      {d.filename}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={d.status} />
                  </TableCell>
                  <TableCell>{d.content_type ?? "—"}</TableCell>
                  <TableCell>{fmt(d.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </ListView>
    </>
  );
}

export default function DocumentsPage() {
  return (
    <Suspense fallback={<TableSkeleton rows={6} />}>
      <DocumentsInner />
    </Suspense>
  );
}
