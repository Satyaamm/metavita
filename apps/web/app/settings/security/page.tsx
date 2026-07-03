"use client";

import {
  Badge,
  Button,
  Caption1,
  Dropdown,
  Field,
  Input,
  Option,
  Spinner,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import { CheckmarkCircleRegular, SaveRegular } from "@fluentui/react-icons";
import { useEffect, useState } from "react";
import { useWorkspaceStore } from "@/lib/stores/settings";
import { appTokens, palette } from "../../theme";

const REGIONS = [
  { value: "global", label: "Global" },
  { value: "us", label: "United States" },
  { value: "eu", label: "European Union" },
];

const CONTROLS = [
  "Encryption in transit (TLS) and at rest (AES-256)",
  "Tenant isolation via workspace scoping + Postgres RLS",
  "Append-only, hash-chained audit log",
  "Malware scanning on every upload",
  "Provider keys encrypted at rest",
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
  controls: { display: "flex", flexDirection: "column", gap: "8px" },
  control: { display: "flex", alignItems: "center", gap: "8px", color: palette.ink },
});

const REGION_LABEL = (v: string) => REGIONS.find((r) => r.value === v)?.label ?? v;

export default function SecuritySettingsPage() {
  const styles = useStyles();
  const { workspace, status, fetch, save } = useWorkspaceStore();
  const [retention, setRetention] = useState("90");
  const [region, setRegion] = useState("global");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch();
  }, [fetch]);

  useEffect(() => {
    if (workspace?.settings) {
      setRetention(String(workspace.settings.retention_days ?? 90));
      setRegion(String(workspace.settings.region ?? "global"));
    }
  }, [workspace]);

  async function submit() {
    setBusy(true);
    setSaved(false);
    try {
      await save({
        settings: {
          ...(workspace?.settings ?? {}),
          retention_days: Number(retention) || 90,
          region,
        },
      });
      setSaved(true);
    } finally {
      setBusy(false);
    }
  }

  if (status === "loading" && !workspace) return <Spinner label="Loading…" />;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div className={styles.panel}>
        <Field label="Data retention (days)" hint="How long documents and logs are kept.">
          <Input type="number" value={retention} onChange={(_, d) => setRetention(d.value)} />
        </Field>
        <Field label="Data residency" hint="Where data is stored and processed.">
          <Dropdown
            value={REGION_LABEL(region)}
            selectedOptions={[region]}
            onOptionSelect={(_, d) => setRegion(d.optionValue as string)}
          >
            {REGIONS.map((r) => (
              <Option key={r.value} value={r.value}>
                {r.label}
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

      <div className={styles.panel}>
        <div className={styles.row}>
          <Text weight="semibold">Compliance controls</Text>
          <Badge appearance="tint" color="success">
            GDPR · SOC 2 · HIPAA-ready
          </Badge>
        </div>
        <div className={styles.controls}>
          {CONTROLS.map((c) => (
            <div key={c} className={styles.control}>
              <CheckmarkCircleRegular style={{ color: "#1F9D55" }} />
              <Caption1 style={{ color: palette.ink }}>{c}</Caption1>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
