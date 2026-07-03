"use client";

import { Badge, Caption1, Text, makeStyles } from "@fluentui/react-components";
import { BotRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect } from "react";
import { EmptyState } from "@/components/EmptyState";
import { HeaderAction } from "@/components/HeaderAction";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import { StatusBadge } from "@/components/StatusBadge";
import { useAgentsStore } from "@/lib/stores/build";
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
    background: `linear-gradient(135deg, ${tints.lilac}, ${tints.rose})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "20px",
  },
  meta: { color: palette.inkSubtle },
});

export default function AgentsPage() {
  const styles = useStyles();
  const { items, status, fetch } = useAgentsStore();

  useEffect(() => {
    fetch();
  }, [fetch]);

  return (
    <>
      <PageHeader
        title="Agents"
        description="Wrap retrieval in an agent — system prompt, model, tools, memory, and attached knowledge."
        actions={<HeaderAction href="/agents/new" label="New agent" />}
      />

      {(status === "idle" || status === "loading") && <CardGridSkeleton count={6} />}

      {status === "ready" && items.length === 0 && (
        <EmptyState
          icon={<BotRegular />}
          title="No agents yet"
          description="Create an agent grounded in your indexes, give it tools, and test it in the playground."
          actionLabel="New agent"
          actionHref="/agents/new"
        />
      )}

      {status === "ready" && items.length > 0 && (
        <div className={styles.grid}>
          {items.map((a) => (
            <Link key={a.id} href={`/agents/${a.id}`} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.icon}>
                  <BotRegular />
                </span>
                <StatusBadge status={a.status} />
              </div>
              <Text weight="semibold">{a.name}</Text>
              <Caption1 className={styles.meta}>{a.model}</Caption1>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <Badge appearance="tint" color="informative">
                  {a.tools.length} tools
                </Badge>
                {a.memory && (
                  <Badge appearance="tint" color="brand">
                    memory
                  </Badge>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
