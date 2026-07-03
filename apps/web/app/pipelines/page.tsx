"use client";

import { Badge, Caption1, Text, makeStyles } from "@fluentui/react-components";
import { FlowchartRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect } from "react";
import { EmptyState } from "@/components/EmptyState";
import { HeaderAction } from "@/components/HeaderAction";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import { StatusBadge } from "@/components/StatusBadge";
import { usePipelinesStore } from "@/lib/stores/build";
import { appTokens, palette, tints } from "../theme";

const useStyles = makeStyles({
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "18px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    textDecoration: "none",
    color: palette.ink,
    transitionProperty: "transform",
    transitionDuration: "150ms",
    ":hover": { transform: "translateY(-2px)" },
  },
  top: { display: "flex", alignItems: "center", justifyContent: "space-between" },
  icon: {
    width: "40px",
    height: "40px",
    borderRadius: "12px",
    background: `linear-gradient(135deg, ${tints.sky}, ${tints.sage})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "20px",
  },
  meta: { color: palette.inkSubtle },
});

export default function PipelinesPage() {
  const styles = useStyles();
  const { items, status, fetch } = usePipelinesStore();

  useEffect(() => {
    fetch();
  }, [fetch]);

  return (
    <>
      <PageHeader
        title="Pipelines"
        description="Assemble retrieval flows visually — source, chunk, embed, retrieve, rerank, LLM — with a code view underneath."
        actions={<HeaderAction href="/pipelines/new" label="New pipeline" />}
      />

      {(status === "idle" || status === "loading") && <CardGridSkeleton count={6} />}

      {status === "ready" && items.length === 0 && (
        <EmptyState
          icon={<FlowchartRegular />}
          title="No pipelines yet"
          description="Build a RAG flow on the visual canvas, then run and publish it."
          actionLabel="New pipeline"
          actionHref="/pipelines/new"
        />
      )}

      {status === "ready" && items.length > 0 && (
        <div className={styles.grid}>
          {items.map((p) => (
            <Link key={p.id} href={`/pipelines/${p.id}`} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.icon}>
                  <FlowchartRegular />
                </span>
                <StatusBadge status={p.status} />
              </div>
              <Text weight="semibold">{p.name}</Text>
              <div style={{ display: "flex", gap: 6 }}>
                <Badge appearance="tint" color="informative">
                  {p.graph?.nodes?.length ?? 0} nodes
                </Badge>
                <Badge appearance="tint" color="subtle">
                  v{p.version}
                </Badge>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
