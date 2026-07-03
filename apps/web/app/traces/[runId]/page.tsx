"use client";

import { Badge, Body1, Caption1, Spinner, Text, makeStyles } from "@fluentui/react-components";
import { ArrowLeftRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { type RunItem, api } from "@/lib/api";
import { appTokens, palette, tints } from "../../theme";

const TINT: Record<string, string> = {
  embed: tints.sky,
  retrieve: tints.sage,
  llm: tints.peach,
  rerank: tints.lilac,
};

const useStyles = makeStyles({
  back: { display: "inline-flex", alignItems: "center", gap: "6px", color: palette.inkSubtle, textDecoration: "none" },
  metaRow: { display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" },
  spans: { display: "flex", flexDirection: "column", gap: "10px" },
  span: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "14px 16px",
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  dot: { width: "12px", height: "12px", borderRadius: "4px", flexShrink: 0 },
  spanMain: { flex: 1, display: "flex", flexDirection: "column", gap: "2px" },
  detail: { color: palette.inkSubtle, fontFamily: "ui-monospace, Menlo, monospace", fontSize: "12px" },
  answer: {
    whiteSpace: "pre-wrap",
    backgroundColor: palette.canvas,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusControl,
    padding: "14px",
  },
});

export default function TraceDetailPage() {
  const styles = useStyles();
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RunItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getRun(runId).then(setRun).catch((e) => setError(String(e)));
  }, [runId]);

  const answer = run?.output?.answer as string | undefined;

  return (
    <>
      <Link href="/traces" className={styles.back}>
        <ArrowLeftRegular /> Traces
      </Link>

      <PageHeader
        title="Trace"
        description={(run?.input?.question as string) ?? "Execution span tree."}
      />

      {error && <Text style={{ color: palette.danger }}>{error}</Text>}
      {!run && !error && <Spinner label="Loading trace…" />}

      {run && (
        <>
          <div className={styles.metaRow}>
            <StatusBadge status={run.status} />
            <Badge appearance="tint" color="subtle">
              {run.kind}
            </Badge>
            {run.latency_ms != null && (
              <Badge appearance="tint" color="informative">
                {run.latency_ms} ms
              </Badge>
            )}
            <Badge appearance="tint" color="subtle">
              {run.tokens_in}/{run.tokens_out} tokens
            </Badge>
          </div>

          <Text weight="semibold">Spans</Text>
          <div className={styles.spans}>
            {(run.spans ?? []).map((s) => (
              <div key={s.seq} className={styles.span}>
                <span className={styles.dot} style={{ background: TINT[s.node_type ?? ""] ?? tints.slate }} />
                <div className={styles.spanMain}>
                  <Text weight="semibold" size={300}>
                    {s.name}
                  </Text>
                  <Caption1 className={styles.detail}>
                    {s.node_type} · {JSON.stringify(s.detail)}
                  </Caption1>
                </div>
                <Caption1 style={{ color: palette.inkSubtle }}>
                  {s.latency_ms != null ? `${s.latency_ms} ms` : ""}
                </Caption1>
              </div>
            ))}
          </div>

          {answer && (
            <>
              <Text weight="semibold">Output</Text>
              <Body1 className={styles.answer}>{answer}</Body1>
            </>
          )}
        </>
      )}
    </>
  );
}
