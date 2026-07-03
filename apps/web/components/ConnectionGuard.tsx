"use client";

import {
  Button,
  MessageBar,
  MessageBarActions,
  MessageBarBody,
  MessageBarTitle,
} from "@fluentui/react-components";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const LABELS: Record<string, string> = {
  llm: "an LLM provider",
  embeddings: "an embedding provider",
  vector_store: "a vector store",
  video: "a video provider",
  rerank: "a rerank provider",
  email: "an email provider",
};

function phrase(caps: string[]): string {
  const parts = caps.map((c) => LABELS[c] ?? c);
  if (parts.length === 1) return parts[0];
  if (parts.length === 2) return `${parts[0]} and ${parts[1]}`;
  return `${parts.slice(0, -1).join(", ")}, and ${parts[parts.length - 1]}`;
}

/**
 * Returns the subset of `need` capabilities that have NO connection in the
 * workspace. `null` while still loading. Pure BYO: every capability must be
 * brought by the user before it can be used.
 */
export function useMissingCapabilities(need: string[]): string[] | null {
  const key = need.join(",");
  const [missing, setMissing] = useState<string[] | null>(null);

  useEffect(() => {
    let alive = true;
    Promise.all(
      need.map((c) =>
        api
          .listConnections({ capability: c })
          .then((r) => [c, r.items.length > 0] as const)
          .catch(() => [c, false] as const),
      ),
    ).then((res) => {
      if (alive) setMissing(res.filter(([, ok]) => !ok).map(([c]) => c));
    });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return missing;
}

/** Presentational banner from an already-computed `missing` list (no fetch). */
export function CapabilityBanner({
  missing,
  action,
  intent = "warning",
}: {
  missing: string[] | null;
  action: string;
  intent?: "warning" | "info";
}) {
  if (!missing || missing.length === 0) return null;
  return (
    <MessageBar intent={intent}>
      <MessageBarBody>
        <MessageBarTitle>
          {intent === "warning" ? "Connection required" : "Recommended"}
        </MessageBarTitle>
        {intent === "warning"
          ? `Connect ${phrase(missing)} before you can ${action} — MetaVita runs on your own provider.`
          : `Connect ${phrase(missing)} to ${action}. A basic offline fallback is used otherwise.`}
      </MessageBarBody>
      <MessageBarActions>
        <Link href="/connections">
          <Button size="small">Go to Connections</Button>
        </Link>
      </MessageBarActions>
    </MessageBar>
  );
}

/**
 * Self-contained guard: fetches + warns when required capabilities aren't
 * connected yet, with a shortcut to Connections. Renders nothing when ready.
 */
export function ConnectionGuard({
  need,
  action,
  intent = "warning",
}: {
  need: string[];
  action: string;
  intent?: "warning" | "info";
}) {
  const missing = useMissingCapabilities(need);
  return <CapabilityBanner missing={missing} action={action} intent={intent} />;
}
