"use client";

import { Badge, Caption1, Subtitle2, Text, makeStyles } from "@fluentui/react-components";
import { DataPieRegular } from "@fluentui/react-icons";
import { useEffect } from "react";
import { BarChart } from "@/components/BarChart";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import { useAnalyticsStore } from "@/lib/stores/overview";
import { appTokens, palette, tints } from "../theme";

const useStyles = makeStyles({
  stats: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "14px" },
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
  value: { fontSize: "24px", fontWeight: 700, lineHeight: 1 },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  kinds: { display: "flex", gap: "8px", flexWrap: "wrap" },
});

export default function AnalyticsPage() {
  const styles = useStyles();
  const { data, status, fetch } = useAnalyticsStore();

  useEffect(() => {
    fetch(14);
  }, [fetch]);

  if (status === "loading" || status === "idle") {
    return (
      <>
        <PageHeader title="Analytics" description="Usage at a glance — volume, latency, cost." />
        <CardGridSkeleton count={4} />
      </>
    );
  }

  const t = data?.totals;
  const successRate = t && t.runs > 0 ? `${Math.round((t.succeeded / t.runs) * 100)}%` : "—";

  return (
    <>
      <PageHeader
        title="Analytics"
        description="Usage at a glance — run volume, latency, tokens, and estimated cost over the last 14 days."
      />

      {t && t.runs === 0 ? (
        <EmptyState
          icon={<DataPieRegular />}
          title="No usage to chart yet"
          description="Run a pipeline, query, or deployment and the analytics will populate here."
        />
      ) : (
        <>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <div className={styles.value}>{t?.runs}</div>
              <Caption1 style={{ color: palette.inkSubtle }}>Total runs</Caption1>
            </div>
            <div className={styles.stat}>
              <div className={styles.value}>{successRate}</div>
              <Caption1 style={{ color: palette.inkSubtle }}>Success rate</Caption1>
            </div>
            <div className={styles.stat}>
              <div className={styles.value}>{t?.avg_latency_ms != null ? `${t.avg_latency_ms}ms` : "—"}</div>
              <Caption1 style={{ color: palette.inkSubtle }}>Avg latency</Caption1>
            </div>
            <div className={styles.stat}>
              <div className={styles.value}>
                {((t?.tokens_in ?? 0) + (t?.tokens_out ?? 0)).toLocaleString()}
              </div>
              <Caption1 style={{ color: palette.inkSubtle }}>Tokens</Caption1>
            </div>
            <div className={styles.stat}>
              <div className={styles.value}>
                {t?.est_cost_usd != null ? `$${t.est_cost_usd}` : "—"}
              </div>
              <Caption1 style={{ color: palette.inkSubtle }}>Est. cost</Caption1>
            </div>
          </div>

          <div className={styles.card}>
            <Subtitle2>Runs per day</Subtitle2>
            <BarChart
              data={(data?.daily ?? []).map((d) => ({ label: d.date.slice(5), value: d.runs }))}
            />
          </div>

          <div className={styles.card}>
            <Subtitle2>By type</Subtitle2>
            {data && Object.keys(data.by_kind).length > 0 ? (
              <div className={styles.kinds}>
                {Object.entries(data.by_kind).map(([kind, n]) => (
                  <Badge key={kind} appearance="tint" color="brand" style={{ background: tints.lilac }}>
                    {kind}: {n}
                  </Badge>
                ))}
              </div>
            ) : (
              <Text style={{ color: palette.inkSubtle }}>No runs yet.</Text>
            )}
          </div>
        </>
      )}
    </>
  );
}
