"use client";

import {
  Badge,
  Button,
  Caption1,
  Input,
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Spinner,
  Text,
  makeStyles,
  mergeClasses,
} from "@fluentui/react-components";
import {
  ArrowLeftRegular,
  ArrowUploadRegular,
  CloudRegular,
  DocumentRegular,
  GlobeRegular,
} from "@fluentui/react-icons";
import Link from "next/link";
import { useRef, useState } from "react";
import { CapabilityBanner, useMissingCapabilities } from "@/components/ConnectionGuard";
import { PageHeader } from "@/components/PageHeader";
import { ApiError, type SourceType, api } from "@/lib/api";
import type { FlagKey } from "@/lib/featureFlags";
import { useUIStore } from "@/lib/stores/ui";
import { appTokens, palette, tints } from "../../../theme";

const useStyles = makeStyles({
  typeGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", maxWidth: "760px" },
  typeCard: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    cursor: "pointer",
    transitionProperty: "transform, border-color",
    transitionDuration: "150ms",
    ":hover": { transform: "translateY(-2px)", border: `1px solid ${palette.brandPrimary}` },
  },
  icon: {
    width: "44px",
    height: "44px",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "22px",
    color: palette.brandPrimary,
  },
  cardTitle: { fontWeight: 600 },
  panel: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "24px",
    maxWidth: "640px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  dropzone: {
    border: `1.5px dashed ${palette.brandPrimary}55`,
    backgroundColor: "#FAFAFE",
    borderRadius: appTokens.radiusControl,
    padding: "28px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "10px",
    textAlign: "center",
  },
  dropIcon: { fontSize: "28px", color: palette.brandPrimary },
  row: { display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" },
  back: { alignSelf: "flex-start" },
});

interface TypeDef {
  key: SourceType;
  title: string;
  desc: string;
  icon: React.ReactNode;
  tint: string;
  flag?: FlagKey;
}

const TYPES: TypeDef[] = [
  { key: "upload", title: "Upload", desc: "PDF, DOCX, Markdown, HTML, or video", icon: <DocumentRegular />, tint: tints.lilac },
  { key: "web", title: "Web page", desc: "Crawl and index a URL", icon: <GlobeRegular />, tint: tints.sky, flag: "webCrawl" },
  { key: "connector", title: "Connector", desc: "Google Drive, Notion, S3, Confluence", icon: <CloudRegular />, tint: tints.peach, flag: "connectors" },
];

export default function NewSourcePage() {
  const styles = useStyles();
  const flags = useUIStore((s) => s.flags);
  const [type, setType] = useState<SourceType | null>(null);

  const enabled = (t: TypeDef) => !t.flag || flags[t.flag];

  return (
    <>
      <PageHeader title="Add a data source" description="Choose how to bring data in." />
      {type === null ? (
        <div className={styles.typeGrid}>
          {TYPES.map((t) => {
            const on = enabled(t);
            return (
              <button
                key={t.key}
                type="button"
                className={styles.typeCard}
                disabled={!on}
                style={!on ? { opacity: 0.6, cursor: "not-allowed" } : undefined}
                onClick={() => on && setType(t.key)}
              >
                <span className={styles.icon} style={{ backgroundColor: t.tint }}>
                  {t.icon}
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Text className={styles.cardTitle}>{t.title}</Text>
                  {!on && (
                    <Badge appearance="tint" color="subtle" size="small">
                      Soon
                    </Badge>
                  )}
                </div>
                <Caption1 style={{ color: palette.inkSubtle }}>{t.desc}</Caption1>
              </button>
            );
          })}
        </div>
      ) : (
        <>
          <Button
            className={styles.back}
            appearance="subtle"
            icon={<ArrowLeftRegular />}
            onClick={() => setType(null)}
          >
            Choose a different type
          </Button>
          {type === "upload" && <UploadPanel />}
          {type === "web" && <WebPanel />}
          {type === "connector" && <ConnectorPanel />}
        </>
      )}
    </>
  );
}

function UploadPanel() {
  const styles = useStyles();
  const fileRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; msg: string; id?: string } | null>(null);
  // Indexing embeds every chunk — an embedding connection is required.
  const missing = useMissingCapabilities(["embeddings"]);
  const blocked = (missing?.length ?? 0) > 0;

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setResult({ ok: false, msg: "Choose a file first." });
      return;
    }
    setBusy(true);
    setResult(null);
    try {
      const r = await api.uploadFile(file);
      setResult({ ok: true, msg: `Indexed ${r.filename} — ${r.chunks} chunks.`, id: r.document_id });
    } catch (e) {
      let msg = `Upload failed: ${String(e)}`;
      if (e instanceof ApiError && e.status === 422) {
        msg = `Upload blocked: ${e.message}. (File rejected by the safety scanner.)`;
      } else if (e instanceof ApiError && e.status === 400 && /embedding/i.test(e.message)) {
        msg = "Connect an embedding provider in Connections before indexing documents.";
      }
      setResult({ ok: false, msg });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.panel}>
      <Text weight="semibold" size={400}>
        Upload a document
      </Text>
      <CapabilityBanner missing={missing} action="upload and index documents" />
      <div className={styles.dropzone}>
        <ArrowUploadRegular className={styles.dropIcon} />
        <Text weight="semibold">Drop a file, or browse</Text>
        <Caption1 style={{ color: palette.inkSubtle }}>
          Every upload is virus-scanned and type-checked before indexing.
        </Caption1>
        <div className={styles.row} style={{ justifyContent: "center" }}>
          <input ref={fileRef} type="file" accept=".pdf,.txt,.md,.docx,.html,.mp4,.mov,.webm" />
          <Button
            appearance="primary"
            icon={<ArrowUploadRegular />}
            onClick={upload}
            disabled={busy || blocked}
          >
            Upload &amp; index
          </Button>
          {busy && <Spinner size="tiny" />}
        </div>
      </div>
      {result && (
        <MessageBar intent={result.ok ? "success" : "error"}>
          <MessageBarBody>
            <MessageBarTitle>{result.ok ? "Indexed" : "Could not index"}</MessageBarTitle>
            {result.msg}
          </MessageBarBody>
          {result.ok && (
            <Link href="/knowledge/documents">
              <Button size="small">View documents</Button>
            </Link>
          )}
        </MessageBar>
      )}
    </div>
  );
}

function WebPanel() {
  const styles = useStyles();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function add() {
    if (!url.trim()) return;
    setBusy(true);
    try {
      await api.createSource({ name: url, type: "web" });
      setDone(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.panel}>
      <Text weight="semibold" size={400}>
        Crawl a web page
      </Text>
      <Input
        value={url}
        onChange={(_, d) => setUrl(d.value)}
        placeholder="https://example.com/docs"
        type="url"
      />
      <div className={styles.row}>
        <Button appearance="primary" icon={<GlobeRegular />} onClick={add} disabled={busy || !url}>
          Add source
        </Button>
        {busy && <Spinner size="tiny" />}
      </div>
      {done && (
        <MessageBar intent="success">
          <MessageBarBody>
            <MessageBarTitle>Source added</MessageBarTitle>
            Crawling &amp; indexing for web sources arrives with connectors — the source is registered.
          </MessageBarBody>
        </MessageBar>
      )}
    </div>
  );
}

const CONNECTORS = ["Google Drive", "Notion", "Amazon S3", "Confluence", "Postgres"];

function ConnectorPanel() {
  const styles = useStyles();
  return (
    <div className={styles.panel}>
      <Text weight="semibold" size={400}>
        Connect a service
      </Text>
      <div className={mergeClasses(styles.row)}>
        {CONNECTORS.map((c) => (
          <Button key={c} disabled icon={<CloudRegular />}>
            {c}
          </Button>
        ))}
      </div>
      <Caption1 style={{ color: palette.inkSubtle }}>
        Scheduled connector sync arrives in the connectors milestone.
      </Caption1>
    </div>
  );
}
