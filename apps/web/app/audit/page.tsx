"use client";

import {
  Badge,
  Caption1,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  makeStyles,
} from "@fluentui/react-components";
import { ShieldTaskRegular } from "@fluentui/react-icons";
import { Suspense } from "react";
import { EmptyState } from "@/components/EmptyState";
import { ListView } from "@/components/ListView";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { TableSkeleton } from "@/components/Skeletons";
import { useAuditStore } from "@/lib/stores/overview";
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
  mono: { fontFamily: "ui-monospace, Menlo, monospace", fontSize: "12px", color: palette.inkSubtle },
});

function AuditInner() {
  const styles = useStyles();
  const { items, total, status, error, fetch } = useAuditStore();
  const { page, pageSize, setPage, setPageSize } = usePaginatedList({
    basePath: "/audit",
    fetch,
  });

  return (
    <>
      <PageHeader
        title="Audit log"
        description="An append-only, hash-chained record of every data access, change, and admin action."
      />

      <ListView
        status={status}
        error={error}
        isEmpty={items.length === 0}
        skeleton={<TableSkeleton rows={8} />}
        empty={
          <EmptyState
            icon={<ShieldTaskRegular />}
            title="No audit events yet"
            description="Security and compliance events (ingests, queries, key changes) are recorded here."
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
          <Table aria-label="Audit log">
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Action</TableHeaderCell>
                <TableHeaderCell>Actor</TableHeaderCell>
                <TableHeaderCell>Resource</TableHeaderCell>
                <TableHeaderCell>When</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((e) => (
                <TableRow key={e.id}>
                  <TableCell>
                    <Badge appearance="tint" color="subtle">
                      {e.action}
                    </Badge>
                  </TableCell>
                  <TableCell>{e.actor}</TableCell>
                  <TableCell>
                    <Caption1 className={styles.mono}>
                      {e.resource_type ?? "—"}
                      {e.resource_id ? `:${e.resource_id.slice(0, 8)}` : ""}
                    </Caption1>
                  </TableCell>
                  <TableCell>{e.created_at ? new Date(e.created_at).toLocaleString() : ""}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </ListView>
    </>
  );
}

export default function AuditPage() {
  return (
    <Suspense fallback={<TableSkeleton rows={8} />}>
      <AuditInner />
    </Suspense>
  );
}
