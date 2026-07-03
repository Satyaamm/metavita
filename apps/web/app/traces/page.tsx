"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  makeStyles,
} from "@fluentui/react-components";
import { DataTrendingRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { Suspense } from "react";
import { EmptyState } from "@/components/EmptyState";
import { ListView } from "@/components/ListView";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { TableSkeleton } from "@/components/Skeletons";
import { StatusBadge } from "@/components/StatusBadge";
import { useRunsStore } from "@/lib/stores/runs";
import { usePaginatedList } from "@/lib/usePaginatedList";
import { appTokens, palette } from "../theme";

const useStyles = makeStyles({
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    overflow: "hidden",
  },
  link: { color: palette.brandPrimary, textDecoration: "none", fontWeight: 600 },
});

function TracesInner() {
  const styles = useStyles();
  const { items, total, status, error, fetch } = useRunsStore();
  const { page, pageSize, setPage, setPageSize } = usePaginatedList({
    basePath: "/traces",
    fetch,
  });

  return (
    <>
      <PageHeader
        title="Traces"
        description="Every run as a span tree — retrieved context, tokens, cost, and latency per step."
      />

      <ListView
        status={status}
        error={error}
        isEmpty={items.length === 0}
        skeleton={<TableSkeleton rows={6} />}
        empty={
          <EmptyState
            icon={<DataTrendingRegular />}
            title="No runs yet"
            description="Run a pipeline from its builder and the trace will appear here for inspection."
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
          <Table aria-label="Traces">
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Kind</TableHeaderCell>
                <TableHeaderCell>Question</TableHeaderCell>
                <TableHeaderCell>Latency</TableHeaderCell>
                <TableHeaderCell>Tokens</TableHeaderCell>
                <TableHeaderCell>Started</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>
                    <Link href={`/traces/${r.id}`} className={styles.link}>
                      <StatusBadge status={r.status} />
                    </Link>
                  </TableCell>
                  <TableCell>{r.kind}</TableCell>
                  <TableCell>{String(r.input?.question ?? "—").slice(0, 60)}</TableCell>
                  <TableCell>{r.latency_ms != null ? `${r.latency_ms} ms` : "—"}</TableCell>
                  <TableCell>
                    {r.tokens_in + r.tokens_out > 0 ? `${r.tokens_in}/${r.tokens_out}` : "—"}
                  </TableCell>
                  <TableCell>{r.created_at ? new Date(r.created_at).toLocaleString() : ""}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </ListView>
    </>
  );
}

export default function TracesPage() {
  return (
    <Suspense fallback={<TableSkeleton rows={6} />}>
      <TracesInner />
    </Suspense>
  );
}
