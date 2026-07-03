"use client";

import { Button, Field, Input, Spinner, makeStyles } from "@fluentui/react-components";
import { BotRegular } from "@fluentui/react-icons";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useAgentsStore } from "@/lib/stores/build";
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

export default function NewAgentPage() {
  const styles = useStyles();
  const router = useRouter();
  const create = useAgentsStore((s) => s.create);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const a = await create(name);
      router.replace(`/agents/${a.id}`);
    } catch {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader title="New agent" description="Name it, then configure prompt, model, tools, and knowledge." />
      <div className={styles.panel}>
        <Field label="Agent name" required>
          <Input
            value={name}
            onChange={(_, d) => setName(d.value)}
            placeholder="Support assistant"
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
        </Field>
        <div className={styles.row}>
          <Button appearance="primary" icon={<BotRegular />} onClick={submit} disabled={busy || !name}>
            Create &amp; configure
          </Button>
          {busy && <Spinner size="tiny" />}
        </div>
      </div>
    </>
  );
}
