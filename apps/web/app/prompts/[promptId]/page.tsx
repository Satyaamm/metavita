"use client";

import {
  Badge,
  Button,
  Caption1,
  Field,
  Input,
  Spinner,
  Text,
  Textarea,
  makeStyles,
} from "@fluentui/react-components";
import { ArrowLeftRegular, HistoryRegular, SaveRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { type PromptItem, api } from "@/lib/api";
import { appTokens, palette } from "../../theme";

const useStyles = makeStyles({
  back: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    color: palette.inkSubtle,
    textDecoration: "none",
  },
  grid: { display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: "20px", "@media (max-width: 980px)": { gridTemplateColumns: "1fr" } },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "18px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  history: { display: "flex", flexDirection: "column", gap: "10px", maxHeight: "60vh", overflowY: "auto" },
  ver: {
    border: `1px solid ${appTokens.border}`,
    borderRadius: "10px",
    padding: "10px 12px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    cursor: "pointer",
    background: palette.canvas,
  },
  mono: { fontFamily: "var(--fontFamilyMonospace, monospace)", fontSize: "13px" },
});

export default function PromptDetailPage() {
  const styles = useStyles();
  const { promptId } = useParams<{ promptId: string }>();
  const [prompt, setPrompt] = useState<PromptItem | null>(null);
  const [content, setContent] = useState("");
  const [notes, setNotes] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const p = await api.getPrompt(promptId);
    setPrompt(p);
    setContent(p.content ?? "");
    setName(p.name);
  }, [promptId]);

  useEffect(() => {
    load();
  }, [load]);

  async function saveVersion() {
    if (!content.trim()) return;
    setBusy(true);
    try {
      if (name.trim() && name !== prompt?.name) await api.updatePrompt(promptId, { name: name.trim() });
      await api.addPromptVersion(promptId, { content, notes });
      setNotes("");
      await load();
    } finally {
      setBusy(false);
    }
  }

  if (!prompt) return <Spinner label="Loading prompt…" />;

  const dirty = content !== (prompt.content ?? "");

  return (
    <>
      <Link href="/prompts" className={styles.back}>
        <ArrowLeftRegular /> Prompts
      </Link>
      <PageHeader
        title={prompt.name}
        description={prompt.description || "Edit the content and save to create a new version."}
        actions={
          <Badge appearance="tint" color="brand">
            v{prompt.current_version}
          </Badge>
        }
      />

      <div className={styles.grid}>
        <div className={styles.card}>
          <Field label="Name">
            <Input value={name} onChange={(_, d) => setName(d.value)} />
          </Field>
          <Field label="Content">
            <Textarea
              className={styles.mono}
              value={content}
              onChange={(_, d) => setContent(d.value)}
              rows={14}
            />
          </Field>
          <Field label="Version notes" hint="What changed in this version?">
            <Input value={notes} onChange={(_, d) => setNotes(d.value)} placeholder="Tightened tone" />
          </Field>
          <div>
            <Button
              appearance="primary"
              icon={<SaveRegular />}
              onClick={saveVersion}
              disabled={busy || !content.trim() || (!dirty && name === prompt.name)}
            >
              {busy ? "Saving…" : `Save as v${prompt.current_version + 1}`}
            </Button>
          </div>
        </div>

        <div className={styles.card}>
          <Text weight="semibold">
            <HistoryRegular style={{ verticalAlign: "-3px", marginRight: 6 }} />
            Version history
          </Text>
          <div className={styles.history}>
            {(prompt.versions ?? []).map((v) => (
              <button
                key={v.version}
                type="button"
                className={styles.ver}
                onClick={() => setContent(v.content)}
                title="Load this version into the editor"
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Text weight="semibold">v{v.version}</Text>
                  <Caption1 style={{ color: palette.inkSubtle }}>
                    {v.created_at ? new Date(v.created_at).toLocaleString() : ""}
                  </Caption1>
                </div>
                {v.notes && <Caption1 style={{ color: palette.inkSubtle }}>{v.notes}</Caption1>}
              </button>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
