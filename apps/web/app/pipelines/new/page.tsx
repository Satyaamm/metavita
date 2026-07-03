"use client";

import { Button, Field, Input, Spinner, makeStyles } from "@fluentui/react-components";
import { FlowchartRegular } from "@fluentui/react-icons";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { usePipelinesStore } from "@/lib/stores/build";
import { appTokens } from "../../theme";

const useStyles = makeStyles({
  panel: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "24px",
    maxWidth: "520px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  row: { display: "flex", gap: "10px", alignItems: "center" },
});

export default function NewPipelinePage() {
  const styles = useStyles();
  const router = useRouter();
  const create = usePipelinesStore((s) => s.create);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const p = await create(name);
      router.replace(`/pipelines/${p.id}`);
    } catch {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader title="New pipeline" description="Name it, then build the flow on the canvas." />
      <div className={styles.panel}>
        <Field label="Pipeline name" required>
          <Input
            value={name}
            onChange={(_, d) => setName(d.value)}
            placeholder="Docs RAG"
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
        </Field>
        <div className={styles.row}>
          <Button appearance="primary" icon={<FlowchartRegular />} onClick={submit} disabled={busy || !name}>
            Create &amp; open builder
          </Button>
          {busy && <Spinner size="tiny" />}
        </div>
      </div>
    </>
  );
}
