"use client";

import {
  Badge,
  Button,
  Caption1,
  Dropdown,
  Option,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import {
  ArrowLeftRegular,
  CheckmarkCircleFilled,
  DismissCircleRegular,
  PlayRegular,
} from "@fluentui/react-icons";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { type EvalDatasetItem, type EvalRunItem, api } from "@/lib/api";
import { usePipelinesStore } from "@/lib/stores/build";
import { appTokens, palette, tints } from "../../theme";

const useStyles = makeStyles({
  back: { display: "inline-flex", alignItems: "center", gap: "6px", color: palette.inkSubtle, textDecoration: "none" },
  bar: { display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" },
  stats: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "12px" },
  stat: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  statValue: { fontSize: "22px", fontWeight: 700, lineHeight: 1 },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    overflow: "hidden",
  },
});

function yes(v: boolean) {
  return v ? (
    <CheckmarkCircleFilled style={{ color: "#1F9D55" }} />
  ) : (
    <DismissCircleRegular style={{ color: "#C44" }} />
  );
}

export default function EvalDetailPage() {
  const styles = useStyles();
  const { evalId } = useParams<{ evalId: string }>();
  const pipelines = usePipelinesStore((s) => s.items);
  const fetchPipelines = usePipelinesStore((s) => s.fetch);

  const [dataset, setDataset] = useState<EvalDatasetItem | null>(null);
  const [pipelineId, setPipelineId] = useState("");
  const [running, setRunning] = useState(false);
  const [run, setRun] = useState<EvalRunItem | null>(null);
  const [past, setPast] = useState<EvalRunItem[]>([]);

  useEffect(() => {
    api.getDataset(evalId).then(setDataset);
    fetchPipelines();
    api.listEvalRuns(evalId).then((r) => setPast(r.items));
  }, [evalId, fetchPipelines]);

  async function go() {
    if (!pipelineId) return;
    setRunning(true);
    try {
      const r = await api.runEval(evalId, { pipeline_id: pipelineId });
      setRun(r);
      setPast((p) => [r, ...p]);
    } finally {
      setRunning(false);
    }
  }

  const summary = run?.summary;
  const pct = (n: number) => (summary?.count ? `${Math.round((n / summary.count) * 100)}%` : "—");

  return (
    <>
      <Link href="/evals" className={styles.back}>
        <ArrowLeftRegular /> Evals
      </Link>
      <PageHeader
        title={dataset?.name ?? "Dataset"}
        description={`${dataset?.item_count ?? 0} questions · run against a pipeline to score it.`}
        actions={
          <div className={styles.bar}>
            <Dropdown
              placeholder="Pick a pipeline"
              value={pipelines.find((p) => p.id === pipelineId)?.name ?? ""}
              selectedOptions={[pipelineId]}
              onOptionSelect={(_, d) => setPipelineId(d.optionValue as string)}
              style={{ minWidth: 200 }}
            >
              {pipelines.map((p) => (
                <Option key={p.id} value={p.id}>
                  {p.name}
                </Option>
              ))}
            </Dropdown>
            <Button appearance="primary" icon={<PlayRegular />} onClick={go} disabled={running || !pipelineId}>
              {running ? "Running…" : "Run eval"}
            </Button>
            {running && <Spinner size="tiny" />}
          </div>
        }
      />

      {summary && (
        <div className={styles.stats}>
          <div className={styles.stat}>
            <div className={styles.statValue}>{summary.count}</div>
            <Caption1 style={{ color: palette.inkSubtle }}>Questions</Caption1>
          </div>
          <div className={styles.stat}>
            <div className={styles.statValue}>{pct(summary.grounded)}</div>
            <Caption1 style={{ color: palette.inkSubtle }}>Grounded</Caption1>
          </div>
          <div className={styles.stat}>
            <div className={styles.statValue}>{pct(summary.with_citations)}</div>
            <Caption1 style={{ color: palette.inkSubtle }}>With citations</Caption1>
          </div>
          <div className={styles.stat}>
            <div className={styles.statValue}>
              {summary.avg_keyword_overlap != null ? summary.avg_keyword_overlap : "—"}
            </div>
            <Caption1 style={{ color: palette.inkSubtle }}>Avg overlap</Caption1>
          </div>
          <div className={styles.stat}>
            <div className={styles.statValue}>
              {summary.avg_latency_ms != null ? `${summary.avg_latency_ms}ms` : "—"}
            </div>
            <Caption1 style={{ color: palette.inkSubtle }}>Avg latency</Caption1>
          </div>
        </div>
      )}

      {run?.results && (
        <div className={styles.card}>
          <Table aria-label="Results">
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Question</TableHeaderCell>
                <TableHeaderCell>Answer</TableHeaderCell>
                <TableHeaderCell>Grounded</TableHeaderCell>
                <TableHeaderCell>Cited</TableHeaderCell>
                <TableHeaderCell>Overlap</TableHeaderCell>
                <TableHeaderCell>Latency</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {run.results.map((r, i) => (
                <TableRow key={i}>
                  <TableCell>{r.question}</TableCell>
                  <TableCell>{r.answer.slice(0, 80)}</TableCell>
                  <TableCell>{yes(r.score.grounded)}</TableCell>
                  <TableCell>{yes(r.score.has_citations)}</TableCell>
                  <TableCell>{r.score.keyword_overlap ?? "—"}</TableCell>
                  <TableCell>{r.latency_ms}ms</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {past.length > 0 && (
        <>
          <Text weight="semibold">Past runs</Text>
          <div className={styles.bar} style={{ flexDirection: "column", alignItems: "stretch", gap: 8 }}>
            {past.map((p) => (
              <Link
                key={p.id}
                href={`/traces`}
                onClick={(e) => {
                  e.preventDefault();
                  api.getEvalRun(p.id).then(setRun);
                }}
                style={{
                  textDecoration: "none",
                  color: palette.ink,
                  border: `1px solid ${appTokens.border}`,
                  borderRadius: 8,
                  padding: "10px 14px",
                  background: tints.sage,
                }}
              >
                <Caption1>
                  {p.created_at ? new Date(p.created_at).toLocaleString() : ""} · {p.summary.count}{" "}
                  questions · {p.summary.grounded} grounded
                </Caption1>
              </Link>
            ))}
          </div>
          <Badge appearance="tint" color="subtle" style={{ alignSelf: "flex-start" }}>
            Click a past run to reload its results
          </Badge>
        </>
      )}
    </>
  );
}
