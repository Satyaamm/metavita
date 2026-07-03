"use client";

import {
  Body1,
  Button,
  Caption1,
  Skeleton,
  SkeletonItem,
  Spinner,
  Subtitle2,
  Text,
  Textarea,
  makeStyles,
} from "@fluentui/react-components";
import {
  ArrowRightRegular,
  ArrowTrendingRegular,
  BotRegular,
  ChatSparkleRegular,
  DatabaseRegular,
  DocumentRegular,
  DocumentTextRegular,
  LayerRegular,
  SendRegular,
} from "@fluentui/react-icons";
import Link from "next/link";
import { type ReactNode, useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import type { AuditEvent, Citation, OverviewStats } from "@/lib/api";
import { useAuditStore, useOverviewStore } from "@/lib/stores/overview";
import { appTokens, palette, tints } from "./theme";

const useStyles = makeStyles({
  page: { display: "flex", flexDirection: "column", gap: "20px", maxWidth: "1180px" },
  statRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "16px",
    "@media (max-width: 980px)": { gridTemplateColumns: "repeat(2, 1fr)" },
  },
  stat: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    padding: "18px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    boxShadow: appTokens.shadowCard,
  },
  iconCircle: {
    width: "40px",
    height: "40px",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "20px",
    color: palette.brandPrimary,
  },
  statValue: { fontSize: "26px", fontWeight: 700, letterSpacing: "-0.01em", lineHeight: 1 },
  statLabel: { color: palette.inkSubtle },
  grid: {
    display: "grid",
    gridTemplateColumns: "1.6fr 1fr",
    gap: "20px",
    alignItems: "start",
    "@media (max-width: 980px)": { gridTemplateColumns: "1fr" },
  },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "22px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  cardHead: { display: "flex", alignItems: "center", gap: "10px" },
  cardHeadIcon: {
    width: "34px",
    height: "34px",
    borderRadius: "10px",
    background: `linear-gradient(135deg, ${tints.lilac}, ${tints.sky})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
  },
  askRow: { display: "flex", gap: "10px", alignItems: "flex-end" },
  answer: {
    whiteSpace: "pre-wrap",
    backgroundColor: palette.canvas,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusControl,
    padding: "14px",
  },
  citation: { borderLeft: `3px solid ${palette.brandPrimary}`, paddingLeft: "10px", marginTop: "8px" },
  steps: { display: "flex", flexDirection: "column", gap: "10px" },
  step: { display: "flex", alignItems: "center", gap: "12px" },
  stepNum: {
    width: "26px",
    height: "26px",
    borderRadius: "50%",
    backgroundColor: palette.brandSoft,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "13px",
    fontWeight: 700,
    flexShrink: 0,
  },
  activity: { display: "flex", flexDirection: "column", gap: "14px" },
  activityItem: { display: "flex", gap: "12px", alignItems: "flex-start" },
  dot: { width: "10px", height: "10px", borderRadius: "50%", marginTop: "5px", flexShrink: 0 },
});

const STAT_DEFS: { key: keyof OverviewStats; label: string; icon: ReactNode; tint: string }[] = [
  { key: "documents", label: "Documents", icon: <DocumentRegular />, tint: tints.lilac },
  { key: "chunks", label: "Chunks indexed", icon: <DocumentTextRegular />, tint: tints.sky },
  { key: "sources", label: "Data sources", icon: <DatabaseRegular />, tint: tints.peach },
  { key: "indexes", label: "Indexes", icon: <LayerRegular />, tint: tints.sage },
];

const ACTION_META: Record<string, { label: string; tint: string }> = {
  "document.ingested": { label: "Indexed a document", tint: tints.sage },
  "upload.rejected": { label: "Blocked an unsafe upload", tint: "#F2C9C9" },
  "query.answered": { label: "Answered a query", tint: tints.lilac },
  "query.streamed": { label: "Answered a query", tint: tints.lilac },
  "document.created": { label: "Added a document", tint: tints.sky },
};

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const ms = Date.now() - new Date(iso).getTime();
  const m = Math.floor(ms / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function activityLabel(e: AuditEvent): string {
  const base = ACTION_META[e.action]?.label ?? e.action;
  const fn = (e.detail?.filename as string | undefined) ?? null;
  return fn ? `${base} · ${fn}` : base;
}

export default function Dashboard() {
  const styles = useStyles();
  const { stats, status: statsStatus, fetch: fetchStats } = useOverviewStore();
  const { items: events, status: auditStatus, fetch: fetchAudit } = useAuditStore();

  useEffect(() => {
    fetchStats();
    fetchAudit();
  }, [fetchStats, fetchAudit]);

  const hasDocs = (stats?.documents ?? 0) > 0;

  return (
    <div className={styles.page}>
      <PageHeader title="Overview" description="Your knowledge base at a glance." />

      {/* Stats — real, with skeletons */}
      <div className={styles.statRow}>
        {STAT_DEFS.map((s) => (
          <div key={s.key} className={styles.stat}>
            <div className={styles.iconCircle} style={{ backgroundColor: s.tint }}>
              {s.icon}
            </div>
            {statsStatus === "ready" && stats ? (
              <div>
                <div className={styles.statValue}>{stats[s.key].toLocaleString()}</div>
                <Caption1 className={styles.statLabel}>{s.label}</Caption1>
              </div>
            ) : (
              <Skeleton>
                <SkeletonItem style={{ width: "55%", height: 22, marginBottom: 8 }} />
                <SkeletonItem style={{ width: "75%" }} />
              </Skeleton>
            )}
          </div>
        ))}
      </div>

      <div className={styles.grid}>
        {/* Left: ask (real) or getting-started */}
        {hasDocs ? <AskCard /> : <GettingStarted loading={statsStatus !== "ready"} />}

        {/* Right: recent activity (real audit) */}
        <section className={styles.card}>
          <div className={styles.cardHead}>
            <span className={styles.cardHeadIcon}>
              <ArrowTrendingRegular />
            </span>
            <Subtitle2>Recent activity</Subtitle2>
          </div>

          {(auditStatus === "idle" || auditStatus === "loading") && (
            <Skeleton>
              {[0, 1, 2, 3].map((i) => (
                <SkeletonItem key={i} style={{ marginBottom: 14 }} />
              ))}
            </Skeleton>
          )}

          {auditStatus === "ready" && events.length === 0 && (
            <Caption1 style={{ color: palette.inkSubtle }}>
              No activity yet — actions like ingests and queries will show up here.
            </Caption1>
          )}

          {auditStatus === "ready" && events.length > 0 && (
            <div className={styles.activity}>
              {events.map((e) => (
                <div key={e.id} className={styles.activityItem}>
                  <span
                    className={styles.dot}
                    style={{ backgroundColor: ACTION_META[e.action]?.tint ?? tints.slate }}
                  />
                  <div>
                    <Text size={200} block>
                      {activityLabel(e)}
                    </Text>
                    <Caption1 style={{ color: palette.inkSubtle }}>{timeAgo(e.created_at)}</Caption1>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function GettingStarted({ loading }: { loading: boolean }) {
  const styles = useStyles();
  const STEPS = [
    { n: 1, label: "Add a data source", href: "/knowledge/sources/new", icon: <DatabaseRegular /> },
    { n: 2, label: "Create an index", href: "/knowledge/indexes", icon: <LayerRegular /> },
    { n: 3, label: "Build an agent", href: "/agents", icon: <BotRegular /> },
  ];
  return (
    <section className={styles.card}>
      <div className={styles.cardHead}>
        <span className={styles.cardHeadIcon}>
          <ChatSparkleRegular />
        </span>
        <Subtitle2>Get started</Subtitle2>
      </div>
      {loading ? (
        <Skeleton>
          <SkeletonItem style={{ marginBottom: 12 }} />
          <SkeletonItem style={{ marginBottom: 12 }} />
          <SkeletonItem />
        </Skeleton>
      ) : (
        <>
          <Body1 style={{ color: palette.inkSubtle }}>
            Bring your data in, make it retrievable, and ship a grounded agent.
          </Body1>
          <div className={styles.steps}>
            {STEPS.map((s) => (
              <Link key={s.n} href={s.href} style={{ textDecoration: "none" }}>
                <div className={styles.step}>
                  <span className={styles.stepNum}>{s.n}</span>
                  <Text style={{ color: palette.ink, flex: 1 }}>{s.label}</Text>
                  <ArrowRightRegular style={{ color: palette.inkSubtle }} />
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function AskCard() {
  const styles = useStyles();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [asking, setAsking] = useState(false);

  async function ask() {
    if (!question.trim()) return;
    setAsking(true);
    setAnswer("");
    setCitations([]);
    try {
      const res = await fetch("/api/query/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, k: 5 }),
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";
        for (const frame of frames) {
          const ev = frame.match(/^event: (.*)$/m)?.[1];
          const data = frame
            .split("\n")
            .filter((l) => l.startsWith("data: "))
            .map((l) => l.slice(6))
            .join("\n");
          if (ev === "citations") setCitations(JSON.parse(data));
          else if (ev === "token") setAnswer((p) => p + data);
        }
      }
    } catch (e) {
      setAnswer(`Error: ${String(e)}`);
    } finally {
      setAsking(false);
    }
  }

  return (
    <section className={styles.card}>
      <div className={styles.cardHead}>
        <span className={styles.cardHeadIcon}>
          <ChatSparkleRegular />
        </span>
        <Subtitle2>Ask your knowledge base</Subtitle2>
      </div>
      <div className={styles.askRow}>
        <Textarea
          style={{ flex: 1 }}
          value={question}
          onChange={(_, d) => setQuestion(d.value)}
          placeholder="e.g. What are the key findings?"
          resize="vertical"
        />
        <Button appearance="primary" icon={<SendRegular />} onClick={ask} disabled={asking}>
          Ask
        </Button>
        {asking && <Spinner size="tiny" />}
      </div>
      {answer && <Body1 className={styles.answer}>{answer}</Body1>}
      {citations.length > 0 && (
        <div>
          <Caption1>Sources</Caption1>
          {citations.map((c) => (
            <div key={c.marker} className={styles.citation}>
              <Caption1>
                [{c.marker}] {c.snippet}
              </Caption1>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
