"use client";

import {
  Button,
  Caption1,
  Checkbox,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  DialogTrigger,
  Field,
  Input,
  Spinner,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import {
  CloudRegular,
  DatabaseRegular,
  DocumentRegular,
  GlobeRegular,
  VideoRegular,
} from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ConnectionGuard } from "@/components/ConnectionGuard";
import { EmptyState } from "@/components/EmptyState";
import { HeaderAction } from "@/components/HeaderAction";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import { StatusBadge } from "@/components/StatusBadge";
import type { DataSource } from "@/lib/api";
import { useSourcesStore } from "@/lib/stores/knowledge";
import { appTokens, palette, tints } from "../../theme";

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
    transitionProperty: "transform, box-shadow, border-color",
    transitionDuration: "150ms",
    ":hover": { transform: "translateY(-2px)", border: `1px solid ${palette.brandPrimary}55` },
  },
  top: { display: "flex", alignItems: "center", justifyContent: "space-between" },
  icon: {
    width: "40px",
    height: "40px",
    borderRadius: "12px",
    background: `linear-gradient(135deg, ${tints.lilac}, ${tints.sky})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "20px",
  },
  name: { fontWeight: 600 },
  meta: { color: palette.inkSubtle, display: "flex", gap: "8px", alignItems: "center" },
  actions: { display: "flex", gap: "10px", alignItems: "center" },
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "440px" },
});

function CrawlDialog() {
  const styles = useStyles();
  const crawl = useSourcesStore((s) => s.crawl);
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState("1");
  const [sameDomain, setSameDomain] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    if (!/^https?:\/\//.test(url.trim())) {
      setErr("Enter an http(s) URL.");
      return;
    }
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const r = await crawl({
        url: url.trim(),
        max_pages: Number(maxPages) || 1,
        same_domain: sameDomain,
      });
      setResult(`Crawled ${r.documents} page(s), ${r.chunks} chunks indexed.`);
      setUrl("");
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(_, d) => setOpen(d.open)}>
      <DialogTrigger disableButtonEnhancement>
        <Button icon={<GlobeRegular />}>Crawl URL</Button>
      </DialogTrigger>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>Crawl a web page</DialogTitle>
          <DialogContent>
            <div className={styles.form}>
              <Field
                label="URL"
                required
                validationState={err ? "error" : "none"}
                validationMessage={err ?? undefined}
              >
                <Input
                  value={url}
                  onChange={(_, d) => setUrl(d.value)}
                  placeholder="https://docs.example.com"
                />
              </Field>
              <Field label="Max pages" hint="Bounded crawl — up to 50.">
                <Input
                  type="number"
                  value={maxPages}
                  onChange={(_, d) => setMaxPages(d.value)}
                />
              </Field>
              <Checkbox
                checked={sameDomain}
                label="Only follow links on the same domain"
                onChange={(_, d) => setSameDomain(!!d.checked)}
              />
              {result && <Caption1 style={{ color: palette.brandPrimary }}>{result}</Caption1>}
            </div>
          </DialogContent>
          <DialogActions>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="secondary">Close</Button>
            </DialogTrigger>
            <Button appearance="primary" onClick={submit} disabled={busy || !url.trim()}>
              {busy ? "Crawling…" : "Crawl"}
            </Button>
            {busy && <Spinner size="tiny" />}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

function sourceIcon(s: DataSource) {
  if (s.modality === "video") return <VideoRegular />;
  if (s.type === "web") return <GlobeRegular />;
  if (s.type === "connector") return <CloudRegular />;
  if (s.type === "upload") return <DocumentRegular />;
  return <DatabaseRegular />;
}

function VideoDialog() {
  const styles = useStyles();
  const ingestVideo = useSourcesStore((s) => s.ingestVideo);
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    if (!/^https?:\/\//.test(url.trim())) {
      setErr("Enter an http(s) video URL.");
      return;
    }
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const r = await ingestVideo({ url: url.trim(), name: name.trim() || undefined });
      setResult(`Indexed video (${r.chunks} segment).`);
      setUrl("");
      setName("");
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(_, d) => setOpen(d.open)}>
      <DialogTrigger disableButtonEnhancement>
        <Button icon={<VideoRegular />}>Add video</Button>
      </DialogTrigger>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>Ingest a video</DialogTitle>
          <DialogContent>
            <div className={styles.form}>
              <ConnectionGuard
                need={["video"]}
                action="embed videos with your own provider"
                intent="info"
              />
              <Field
                label="Video URL"
                required
                hint="Embedded with your connected video provider (offline fallback otherwise)."
                validationState={err ? "error" : "none"}
                validationMessage={err ?? undefined}
              >
                <Input
                  value={url}
                  onChange={(_, d) => setUrl(d.value)}
                  placeholder="https://cdn.example.com/talk.mp4"
                />
              </Field>
              <Field label="Name">
                <Input value={name} onChange={(_, d) => setName(d.value)} placeholder="Keynote talk" />
              </Field>
              {result && <Caption1 style={{ color: palette.brandPrimary }}>{result}</Caption1>}
            </div>
          </DialogContent>
          <DialogActions>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="secondary">Close</Button>
            </DialogTrigger>
            <Button appearance="primary" onClick={submit} disabled={busy || !url.trim()}>
              {busy ? "Indexing…" : "Ingest"}
            </Button>
            {busy && <Spinner size="tiny" />}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

export default function SourcesPage() {
  const styles = useStyles();
  const { items, status, error, fetch } = useSourcesStore();

  useEffect(() => {
    fetch();
  }, [fetch]);

  return (
    <>
      <PageHeader
        title="Data Sources"
        description="Connect and sync the data your agents retrieve from — files, web pages, video, and connectors."
        actions={
          <div className={styles.actions}>
            <VideoDialog />
            <CrawlDialog />
            <HeaderAction href="/knowledge/sources/new" label="Add a source" />
          </div>
        }
      />

      {error && <Text style={{ color: palette.danger }}>{error}</Text>}

      {(status === "idle" || status === "loading") && <CardGridSkeleton count={6} />}

      {status === "ready" && items.length === 0 && (
        <EmptyState
          icon={<DatabaseRegular />}
          title="No data sources yet"
          description="Upload documents or video, crawl a URL, or connect Google Drive, Notion, S3, and more."
          actionLabel="Add a source"
          actionHref="/knowledge/sources/new"
        />
      )}

      {status === "ready" && items.length > 0 && (
        <div className={styles.grid}>
          {items.map((s) => (
            <Link key={s.id} href={`/knowledge/documents?source_id=${s.id}`} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.icon}>{sourceIcon(s)}</span>
                <StatusBadge status={s.status} />
              </div>
              <div>
                <Text className={styles.name} block>
                  {s.name}
                </Text>
                <Caption1 className={styles.meta}>
                  {s.type}
                  {s.connector ? ` · ${s.connector}` : ""} · {s.modality}
                </Caption1>
              </div>
              <Caption1 className={styles.meta}>
                {s.document_count ?? 0} document{s.document_count === 1 ? "" : "s"}
              </Caption1>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
