"use client";

import { Caption1, SearchBox, Text, makeStyles, tokens } from "@fluentui/react-components";
import {
  Bot20Regular,
  DocumentRegular,
  Flowchart20Regular,
  PlugConnected20Regular,
} from "@fluentui/react-icons";
import { useRouter } from "next/navigation";
import { type ReactNode, useEffect, useMemo, useRef, useState } from "react";
import {
  type AgentItem,
  type ConnectionItem,
  type DocumentItem,
  type PipelineItem,
  api,
} from "@/lib/api";
import { NAV } from "@/lib/nav";
import { appTokens, palette } from "../app/theme";

interface Hit {
  id: string;
  label: string;
  sub?: string;
  href: string;
  icon: ReactNode;
}

const useStyles = makeStyles({
  wrap: { position: "relative", width: "340px", maxWidth: "40vw" },
  results: {
    position: "absolute",
    top: "40px",
    left: 0,
    right: 0,
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    zIndex: 30,
    maxHeight: "70vh",
    overflowY: "auto",
    padding: "6px",
  },
  group: { padding: "4px 0" },
  groupLabel: {
    padding: "4px 10px",
    color: tokens.colorNeutralForeground4,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    fontSize: "10px",
  },
  row: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    width: "100%",
    padding: "8px 10px",
    border: "none",
    background: "transparent",
    cursor: "pointer",
    borderRadius: appTokens.radiusControl,
    textAlign: "left",
    color: palette.ink,
    ":hover": { backgroundColor: tokens.colorNeutralBackground3 },
  },
  rowMeta: { display: "flex", flexDirection: "column", lineHeight: 1.2, minWidth: 0 },
  sub: { color: palette.inkSubtle, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  empty: { padding: "16px 12px", color: palette.inkSubtle },
});

const PAGES: Hit[] = NAV.flatMap((g) =>
  g.items.map((i) => ({
    id: `page:${i.key}`,
    label: i.label,
    sub: g.section,
    href: i.href,
    icon: <i.Icon />,
  })),
);

export function HeaderSearch() {
  const styles = useStyles();
  const router = useRouter();
  const [q, setQ] = useState("");
  const [focused, setFocused] = useState(false);
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [pipelines, setPipelines] = useState<PipelineItem[]>([]);
  const [connections, setConnections] = useState<ConnectionItem[]>([]);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const blurTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Small lists load once; cheap to filter client-side.
  useEffect(() => {
    api.listAgents().then((r) => setAgents(r.items)).catch(() => {});
    api.listPipelines().then((r) => setPipelines(r.items)).catch(() => {});
    api.listConnections().then((r) => setConnections(r.items)).catch(() => {});
  }, []);

  // Documents are searched server-side (debounced).
  useEffect(() => {
    const query = q.trim();
    if (query.length < 2) {
      setDocs([]);
      return;
    }
    const t = setTimeout(() => {
      api.listDocuments({ q: query, limit: 5 }).then((r) => setDocs(r.items)).catch(() => {});
    }, 200);
    return () => clearTimeout(t);
  }, [q]);

  const groups = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return [];
    const match = (s: string) => s.toLowerCase().includes(query);
    const out: { label: string; hits: Hit[] }[] = [];

    const pages = PAGES.filter((p) => match(p.label)).slice(0, 5);
    if (pages.length) out.push({ label: "Pages", hits: pages });

    const conn = connections
      .filter((c) => match(c.name) || match(c.provider_label))
      .slice(0, 5)
      .map<Hit>((c) => ({
        id: `conn:${c.id}`,
        label: c.name,
        sub: c.provider_label,
        href: "/connections",
        icon: <PlugConnected20Regular />,
      }));
    if (conn.length) out.push({ label: "Connections", hits: conn });

    const ag = agents
      .filter((a) => match(a.name))
      .slice(0, 5)
      .map<Hit>((a) => ({
        id: `ag:${a.id}`,
        label: a.name,
        sub: a.model,
        href: `/agents/${a.id}`,
        icon: <Bot20Regular />,
      }));
    if (ag.length) out.push({ label: "Agents", hits: ag });

    const pl = pipelines
      .filter((p) => match(p.name))
      .slice(0, 5)
      .map<Hit>((p) => ({
        id: `pl:${p.id}`,
        label: p.name,
        sub: p.status,
        href: `/pipelines/${p.id}`,
        icon: <Flowchart20Regular />,
      }));
    if (pl.length) out.push({ label: "Pipelines", hits: pl });

    const dh = docs.slice(0, 5).map<Hit>((d) => ({
      id: `doc:${d.id}`,
      label: d.filename,
      sub: d.status,
      href: `/knowledge/documents/${d.id}`,
      icon: <DocumentRegular />,
    }));
    if (dh.length) out.push({ label: "Documents", hits: dh });

    return out;
  }, [q, agents, pipelines, connections, docs]);

  const flat = groups.flatMap((g) => g.hits);

  function go(href: string) {
    setQ("");
    setFocused(false);
    router.push(href);
  }

  const open = focused && q.trim().length > 0;

  return (
    <div className={styles.wrap}>
      <SearchBox
        value={q}
        placeholder="Search documents, agents, connections…"
        appearance="filled-lighter"
        style={{ width: "100%" }}
        onChange={(_, d) => setQ(d.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          blurTimer.current = setTimeout(() => setFocused(false), 150);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" && flat[0]) go(flat[0].href);
          if (e.key === "Escape") setFocused(false);
        }}
      />
      {open && (
        <div
          className={styles.results}
          onMouseDown={() => {
            if (blurTimer.current) clearTimeout(blurTimer.current);
          }}
        >
          {flat.length === 0 ? (
            <div className={styles.empty}>
              <Caption1>No matches for “{q.trim()}”.</Caption1>
            </div>
          ) : (
            groups.map((g) => (
              <div key={g.label} className={styles.group}>
                <div className={styles.groupLabel}>{g.label}</div>
                {g.hits.map((h) => (
                  <button key={h.id} type="button" className={styles.row} onClick={() => go(h.href)}>
                    {h.icon}
                    <span className={styles.rowMeta}>
                      <Text size={300}>{h.label}</Text>
                      {h.sub && <Caption1 className={styles.sub}>{h.sub}</Caption1>}
                    </span>
                  </button>
                ))}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
