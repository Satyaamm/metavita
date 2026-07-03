"use client";

import { Badge, Button, Caption1, Field, Input, Spinner, Text, makeStyles } from "@fluentui/react-components";
import { ArrowLeftRegular, PauseRegular, PlayRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { type DeploymentItem, api } from "@/lib/api";
import { curlSnippet, serveUrl, widgetSnippet } from "@/lib/widget";
import { appTokens, palette } from "../../theme";

const useStyles = makeStyles({
  back: { display: "inline-flex", alignItems: "center", gap: "6px", color: palette.inkSubtle, textDecoration: "none" },
  panel: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "22px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    maxWidth: "760px",
  },
  metaRow: { display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" },
  code: {
    margin: 0,
    padding: "14px",
    borderRadius: appTokens.radiusControl,
    background: "#0E1020",
    color: "#D7DAF0",
    fontFamily: "ui-monospace, Menlo, monospace",
    fontSize: "12.5px",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
  },
});

function apiBase() {
  return typeof window !== "undefined" ? `${window.location.origin}/api` : "";
}

export default function DeploymentDetailPage() {
  const styles = useStyles();
  const { deploymentId } = useParams<{ deploymentId: string }>();
  const [dep, setDep] = useState<DeploymentItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getDeployment(deploymentId).then(setDep).catch((e) => setError(String(e)));
  }, [deploymentId]);

  async function toggle() {
    if (!dep) return;
    const updated =
      dep.status === "active"
        ? await api.pauseDeployment(dep.id)
        : await api.unpauseDeployment(dep.id);
    setDep(updated);
  }

  const base = apiBase();

  return (
    <>
      <Link href="/deployments" className={styles.back}>
        <ArrowLeftRegular /> Deployments
      </Link>

      <PageHeader
        title={dep?.name ?? "Deployment"}
        description="The live serving endpoint, API key, and embed snippet for this deployment."
        actions={
          dep && (
            <Button
              appearance="secondary"
              icon={dep.status === "active" ? <PauseRegular /> : <PlayRegular />}
              onClick={toggle}
            >
              {dep.status === "active" ? "Pause" : "Resume"}
            </Button>
          )
        }
      />

      {error && <Text style={{ color: palette.danger }}>{error}</Text>}
      {!dep && !error && <Spinner label="Loading deployment…" />}

      {dep && (
        <div className={styles.panel}>
          <div className={styles.metaRow}>
            <StatusBadge status={dep.status} />
            <Badge appearance="tint" color="informative">
              {dep.target_type}
            </Badge>
            <Caption1 style={{ color: palette.inkSubtle, fontFamily: "ui-monospace, Menlo, monospace" }}>
              key {dep.key_prefix}…
            </Caption1>
          </div>

          <Field label="Endpoint">
            <Input readOnly value={serveUrl(dep.id, base)} />
          </Field>

          <Field label="cURL" hint="Use the API key shown once when you created this deployment.">
            <pre className={styles.code}>{curlSnippet(dep.id, "mv_YOUR_API_KEY", base)}</pre>
          </Field>

          <Field label="Embed widget" hint="Drop this into any page to add a chat widget.">
            <pre className={styles.code}>{widgetSnippet(dep.id, base)}</pre>
          </Field>
        </div>
      )}
    </>
  );
}
