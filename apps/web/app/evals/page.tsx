"use client";

import {
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
import { AddRegular, ClipboardTaskRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import { parseQuestions, useEvalsStore } from "@/lib/stores/evals";
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
    gap: "10px",
    textDecoration: "none",
    color: palette.ink,
    transitionProperty: "transform",
    transitionDuration: "150ms",
    ":hover": { transform: "translateY(-2px)" },
  },
  icon: {
    width: "40px",
    height: "40px",
    borderRadius: "12px",
    background: `linear-gradient(135deg, ${tints.sage}, ${tints.lilac})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "20px",
  },
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "460px" },
});

export default function EvalsPage() {
  const styles = useStyles();
  const { items, status, fetch, create } = useEvalsStore();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch();
  }, [fetch]);

  async function submit() {
    const qa = parseQuestions(text);
    if (!name.trim() || qa.length === 0) return;
    setBusy(true);
    try {
      await create(name, qa);
      setOpen(false);
      setName("");
      setText("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Evals"
        description="Run a question set through a pipeline and score faithfulness, citations, and latency."
        actions={
          <Dialog open={open} onOpenChange={(_, d) => setOpen(d.open)}>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="primary" icon={<AddRegular />}>
                New dataset
              </Button>
            </DialogTrigger>
            <DialogSurface>
              <DialogBody>
                <DialogTitle>New eval dataset</DialogTitle>
                <DialogContent>
                  <div className={styles.form}>
                    <Field label="Name" required>
                      <Input value={name} onChange={(_, d) => setName(d.value)} placeholder="Support FAQ" />
                    </Field>
                    <Field
                      label="Questions"
                      hint="One per line. Optionally add an expected answer after a | — e.g. 'What is X? | the answer'."
                    >
                      <Textarea
                        value={text}
                        onChange={(_, d) => setText(d.value)}
                        rows={8}
                        placeholder={"What are the key findings?\nWho is the author? | Jane Doe"}
                      />
                    </Field>
                  </div>
                </DialogContent>
                <DialogActions>
                  <DialogTrigger disableButtonEnhancement>
                    <Button appearance="secondary">Cancel</Button>
                  </DialogTrigger>
                  <Button appearance="primary" onClick={submit} disabled={busy || !name || !text.trim()}>
                    {busy ? "Creating…" : "Create"}
                  </Button>
                </DialogActions>
              </DialogBody>
            </DialogSurface>
          </Dialog>
        }
      />

      {(status === "idle" || status === "loading") && <CardGridSkeleton count={4} />}

      {status === "ready" && items.length === 0 && (
        <EmptyState
          icon={<ClipboardTaskRegular />}
          title="No eval datasets yet"
          description="Create a question set, then benchmark a pipeline against it over time."
        />
      )}

      {status === "ready" && items.length > 0 && (
        <div className={styles.grid}>
          {items.map((d) => (
            <Link key={d.id} href={`/evals/${d.id}`} className={styles.card}>
              <span className={styles.icon}>
                <ClipboardTaskRegular />
              </span>
              <Text weight="semibold">{d.name}</Text>
              <Caption1 style={{ color: palette.inkSubtle }}>{d.item_count} questions</Caption1>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
