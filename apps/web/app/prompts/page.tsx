"use client";

import {
  Badge,
  Button,
  Caption1,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  DialogTrigger,
  Field,
  Input,
  Text,
  Textarea,
  makeStyles,
} from "@fluentui/react-components";
import { AddRegular, NotepadRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import { usePromptsStore } from "@/lib/stores/prompts";
import { appTokens, palette, tints } from "../theme";

const useStyles = makeStyles({
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px" },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "18px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
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
    background: `linear-gradient(135deg, ${tints.sky}, ${tints.lilac})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "20px",
  },
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "480px" },
});

export default function PromptsPage() {
  const styles = useStyles();
  const { items, status, fetch, create } = usePromptsStore();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch();
  }, [fetch]);

  async function submit() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await create({ name: name.trim(), description, content });
      setOpen(false);
      setName("");
      setDescription("");
      setContent("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Prompts"
        description="A versioned library of reusable system prompts and templates for agents and pipelines."
        actions={
          <Dialog open={open} onOpenChange={(_, d) => setOpen(d.open)}>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="primary" icon={<AddRegular />}>
                New prompt
              </Button>
            </DialogTrigger>
            <DialogSurface>
              <DialogBody>
                <DialogTitle>New prompt</DialogTitle>
                <DialogContent>
                  <div className={styles.form}>
                    <Field label="Name" required>
                      <Input
                        value={name}
                        onChange={(_, d) => setName(d.value)}
                        placeholder="Support agent system prompt"
                      />
                    </Field>
                    <Field label="Description">
                      <Input
                        value={description}
                        onChange={(_, d) => setDescription(d.value)}
                        placeholder="Friendly, concise, cites sources"
                      />
                    </Field>
                    <Field label="Content" hint="The first version. Edit later to add new versions.">
                      <Textarea
                        value={content}
                        onChange={(_, d) => setContent(d.value)}
                        rows={6}
                        placeholder="You are a helpful support agent…"
                      />
                    </Field>
                  </div>
                </DialogContent>
                <DialogActions>
                  <DialogTrigger disableButtonEnhancement>
                    <Button appearance="secondary">Cancel</Button>
                  </DialogTrigger>
                  <Button appearance="primary" onClick={submit} disabled={busy || !name.trim()}>
                    {busy ? "Creating…" : "Create"}
                  </Button>
                </DialogActions>
              </DialogBody>
            </DialogSurface>
          </Dialog>
        }
      />

      {(status === "idle" || status === "loading") && <CardGridSkeleton count={6} />}

      {status === "ready" && items.length === 0 && (
        <EmptyState
          icon={<NotepadRegular />}
          title="No saved prompts"
          description="Save and version prompts here to reuse them across agents and pipelines."
        />
      )}

      {status === "ready" && items.length > 0 && (
        <div className={styles.grid}>
          {items.map((p) => (
            <Link key={p.id} href={`/prompts/${p.id}`} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.icon}>
                  <NotepadRegular />
                </span>
                <Badge appearance="tint" color="brand">
                  v{p.current_version}
                </Badge>
              </div>
              <Text weight="semibold">{p.name}</Text>
              <Caption1 style={{ color: palette.inkSubtle, minHeight: 32 }}>
                {p.description || "No description."}
              </Caption1>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
