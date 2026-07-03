"use client";

import {
  Button,
  Caption1,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  DialogTrigger,
  Dropdown,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Option,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import { AddRegular, RocketRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { ListView } from "@/components/ListView";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { TableSkeleton } from "@/components/Skeletons";
import { StatusBadge } from "@/components/StatusBadge";
import type { DeploymentCreated } from "@/lib/api";
import { useAgentsStore, usePipelinesStore } from "@/lib/stores/build";
import { useDeploymentsStore } from "@/lib/stores/deployments";
import { usePaginatedList } from "@/lib/usePaginatedList";
import { curlSnippet, serveUrl } from "@/lib/widget";
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
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "440px" },
  code: {
    margin: 0,
    padding: "12px",
    borderRadius: appTokens.radiusControl,
    background: "#0E1020",
    color: "#D7DAF0",
    fontFamily: "ui-monospace, Menlo, monospace",
    fontSize: "12px",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
  },
});

function apiBase() {
  return typeof window !== "undefined" ? `${window.location.origin}/api` : "";
}

function PublishDialog() {
  const styles = useStyles();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [targetType, setTargetType] = useState<"pipeline" | "agent">("pipeline");
  const [targetId, setTargetId] = useState("");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<DeploymentCreated | null>(null);

  const pipelines = usePipelinesStore((s) => s.items);
  const fetchPipelines = usePipelinesStore((s) => s.fetch);
  const agents = useAgentsStore((s) => s.items);
  const fetchAgents = useAgentsStore((s) => s.fetch);
  const create = useDeploymentsStore((s) => s.create);

  useEffect(() => {
    fetchPipelines();
    fetchAgents();
  }, [fetchPipelines, fetchAgents]);

  const targets = targetType === "pipeline" ? pipelines : agents;
  const targetName = targets.find((t) => t.id === targetId)?.name ?? "Select…";

  async function submit() {
    if (!name.trim() || !targetId) return;
    setBusy(true);
    try {
      const d = await create({ name, target_type: targetType, target_id: targetId });
      setCreated(d);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setCreated(null);
    setName("");
    setTargetId("");
  }

  return (
    <Dialog open={open} onOpenChange={(_, d) => { setOpen(d.open); if (!d.open) reset(); }}>
      <DialogTrigger disableButtonEnhancement>
        <Button appearance="primary" icon={<AddRegular />}>
          New deployment
        </Button>
      </DialogTrigger>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{created ? "Deployment live" : "Publish a deployment"}</DialogTitle>
          <DialogContent>
            {created ? (
              <div className={styles.form}>
                <MessageBar intent="warning">
                  <MessageBarBody>
                    <MessageBarTitle>Copy your API key now</MessageBarTitle>
                    It is shown only once.
                  </MessageBarBody>
                </MessageBar>
                <Field label="API key">
                  <Input readOnly value={created.api_key} />
                </Field>
                <Field label="Endpoint">
                  <Input readOnly value={serveUrl(created.id, apiBase())} />
                </Field>
                <Field label="cURL">
                  <pre className={styles.code}>{curlSnippet(created.id, created.api_key, apiBase())}</pre>
                </Field>
              </div>
            ) : (
              <div className={styles.form}>
                <Field label="Name" required>
                  <Input value={name} onChange={(_, d) => setName(d.value)} placeholder="Support API" />
                </Field>
                <Field label="Target type">
                  <Dropdown
                    value={targetType}
                    selectedOptions={[targetType]}
                    onOptionSelect={(_, d) => {
                      setTargetType(d.optionValue as "pipeline" | "agent");
                      setTargetId("");
                    }}
                  >
                    <Option value="pipeline">Pipeline</Option>
                    <Option value="agent">Agent</Option>
                  </Dropdown>
                </Field>
                <Field label={`Target ${targetType}`} required>
                  <Dropdown
                    value={targetName}
                    selectedOptions={[targetId]}
                    onOptionSelect={(_, d) => setTargetId(d.optionValue as string)}
                  >
                    {targets.map((t) => (
                      <Option key={t.id} value={t.id}>
                        {t.name}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
              </div>
            )}
          </DialogContent>
          <DialogActions>
            {created ? (
              <>
                <Link href={`/deployments/${created.id}`}>
                  <Button appearance="primary">Open deployment</Button>
                </Link>
                <Button appearance="secondary" onClick={reset}>
                  Publish another
                </Button>
              </>
            ) : (
              <>
                <DialogTrigger disableButtonEnhancement>
                  <Button appearance="secondary">Cancel</Button>
                </DialogTrigger>
                <Button appearance="primary" onClick={submit} disabled={busy || !name || !targetId}>
                  {busy ? "Publishing…" : "Publish"}
                </Button>
              </>
            )}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

function DeploymentsInner() {
  const styles = useStyles();
  const { items, total, status, error, fetch, setStatus } = useDeploymentsStore();
  const { page, pageSize, setPage, setPageSize } = usePaginatedList({
    basePath: "/deployments",
    fetch,
  });

  return (
    <>
      <PageHeader
        title="Deployments"
        description="Publish an agent or pipeline as a versioned API and embeddable widget."
        actions={<PublishDialog />}
      />

      <ListView
        status={status}
        error={error}
        isEmpty={items.length === 0}
        skeleton={<TableSkeleton rows={5} />}
        empty={
          <EmptyState
            icon={<RocketRegular />}
            title="Nothing deployed yet"
            description="Publish a pipeline or agent to get an API endpoint, key, and embed snippet."
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
          <Table aria-label="Deployments">
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Name</TableHeaderCell>
                <TableHeaderCell>Target</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Key</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((d) => (
                <TableRow key={d.id}>
                  <TableCell>
                    <Link href={`/deployments/${d.id}`} className={styles.link}>
                      {d.name}
                    </Link>
                  </TableCell>
                  <TableCell>{d.target_type}</TableCell>
                  <TableCell>
                    <StatusBadge status={d.status} />
                  </TableCell>
                  <TableCell>
                    <Caption1 style={{ fontFamily: "ui-monospace, Menlo, monospace" }}>
                      {d.key_prefix}…
                    </Caption1>
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      appearance="subtle"
                      onClick={() => setStatus(d.id, d.status === "active" ? "paused" : "active")}
                    >
                      {d.status === "active" ? "Pause" : "Resume"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </ListView>
    </>
  );
}

export default function DeploymentsPage() {
  return (
    <Suspense fallback={<TableSkeleton rows={5} />}>
      <DeploymentsInner />
    </Suspense>
  );
}
