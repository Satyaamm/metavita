"use client";

import {
  Button,
  Caption1,
  Dropdown,
  Field,
  Input,
  Option,
  Spinner,
  makeStyles,
} from "@fluentui/react-components";
import { SaveRegular } from "@fluentui/react-icons";
import { useEffect, useState } from "react";
import { useWorkspaceStore } from "@/lib/stores/settings";
import { appTokens, palette } from "../theme";

const KEY_POLICIES = [
  { value: "platform", label: "Platform-managed (default)" },
  { value: "byo", label: "Bring your own keys" },
  { value: "local", label: "Local models only" },
];

const useStyles = makeStyles({
  panel: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "22px",
    maxWidth: "560px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  row: { display: "flex", gap: "10px", alignItems: "center" },
});

export default function WorkspaceSettingsPage() {
  const styles = useStyles();
  const { workspace, status, fetch, save } = useWorkspaceStore();
  const [name, setName] = useState("");
  const [policy, setPolicy] = useState("platform");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch();
  }, [fetch]);

  useEffect(() => {
    if (workspace) {
      setName(workspace.name);
      setPolicy(workspace.key_policy);
    }
  }, [workspace]);

  async function submit() {
    setBusy(true);
    setSaved(false);
    try {
      await save({ name, key_policy: policy });
      setSaved(true);
    } finally {
      setBusy(false);
    }
  }

  if (status === "loading" && !workspace) return <Spinner label="Loading workspace…" />;

  return (
    <div className={styles.panel}>
      <Field label="Workspace name">
        <Input value={name} onChange={(_, d) => setName(d.value)} />
      </Field>
      <Field label="Key policy" hint="How LLM provider keys are sourced for this workspace.">
        <Dropdown
          value={KEY_POLICIES.find((k) => k.value === policy)?.label ?? policy}
          selectedOptions={[policy]}
          onOptionSelect={(_, d) => setPolicy(d.optionValue as string)}
        >
          {KEY_POLICIES.map((k) => (
            <Option key={k.value} value={k.value}>
              {k.label}
            </Option>
          ))}
        </Dropdown>
      </Field>
      <div className={styles.row}>
        <Button appearance="primary" icon={<SaveRegular />} onClick={submit} disabled={busy}>
          Save
        </Button>
        {busy && <Spinner size="tiny" />}
        {saved && <Caption1 style={{ color: palette.inkSubtle }}>Saved.</Caption1>}
      </div>
    </div>
  );
}
