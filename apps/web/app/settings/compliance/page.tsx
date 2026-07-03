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
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import { PlayRegular, ShieldTaskRegular } from "@fluentui/react-icons";
import { useEffect, useState } from "react";
import { useComplianceStore } from "@/lib/stores/compliance";
import { appTokens, palette } from "../../theme";

const KIND_LABEL: Record<string, string> = {
  export: "Export (portability)",
  erasure: "Erasure (forget)",
};

const STATUS_COLOR: Record<string, "informative" | "success" | "danger"> = {
  pending: "informative",
  completed: "success",
  failed: "danger",
};

const useStyles = makeStyles({
  wrap: { display: "flex", flexDirection: "column", gap: "20px" },
  panel: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "22px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  row: { display: "flex", gap: "10px", alignItems: "flex-end", flexWrap: "wrap" },
  head: { display: "flex", gap: "10px", alignItems: "center" },
});

export default function CompliancePage() {
  const styles = useStyles();
  const { requests, retention, status, fetch, createRequest, process, saveRetention } =
    useComplianceStore();
  const [subject, setSubject] = useState("");
  const [kind, setKind] = useState<"export" | "erasure">("export");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch();
  }, [fetch]);

  async function submit() {
    if (!subject.trim()) return;
    setBusy(true);
    try {
      await createRequest({ subject: subject.trim(), kind });
      setSubject("");
    } finally {
      setBusy(false);
    }
  }

  if (status === "loading" && !retention) return <Spinner label="Loading…" />;

  return (
    <div className={styles.wrap}>
      <div className={styles.panel}>
        <div className={styles.head}>
          <ShieldTaskRegular style={{ color: palette.brandPrimary }} />
          <Text weight="semibold">HIPAA &amp; provider routing</Text>
          <Badge appearance="tint" color="success">
            BAA-gated
          </Badge>
        </div>
        <Caption1 style={{ color: palette.inkSubtle }}>
          When HIPAA mode is on, agents are restricted to providers you&apos;ve signed a BAA
          with; non-BAA endpoints are blocked in the key-routing layer.
        </Caption1>
        <Switch
          checked={!!retention?.hipaa}
          label={retention?.hipaa ? "HIPAA mode enabled" : "HIPAA mode disabled"}
          onChange={(_, d) => saveRetention({ hipaa: d.checked })}
        />
        <Caption1 style={{ color: palette.inkSubtle }}>
          Retention: {retention?.retention_days ?? "—"} days · Region:{" "}
          {retention?.region ?? "global"} · Allowed providers:{" "}
          {retention?.allowed_providers.length ? retention.allowed_providers.join(", ") : "all"}
        </Caption1>
      </div>

      <div className={styles.panel}>
        <Text weight="semibold">Data subject requests (GDPR)</Text>
        <Caption1 style={{ color: palette.inkSubtle }}>
          Export delivers a portable copy of a subject&apos;s data; erasure crypto-shreds documents,
          chunks, and embeddings. Every action is written to the audit log.
        </Caption1>
        <div className={styles.row}>
          <Field label="Subject (email or id)" style={{ flex: 1, minWidth: 220 }}>
            <Input
              value={subject}
              onChange={(_, d) => setSubject(d.value)}
              placeholder="jane@example.com"
            />
          </Field>
          <Field label="Type">
            <Dropdown
              value={KIND_LABEL[kind]}
              selectedOptions={[kind]}
              onOptionSelect={(_, d) => setKind(d.optionValue as "export" | "erasure")}
              style={{ minWidth: 200 }}
            >
              <Option value="export" text={KIND_LABEL.export}>
                {KIND_LABEL.export}
              </Option>
              <Option value="erasure" text={KIND_LABEL.erasure}>
                {KIND_LABEL.erasure}
              </Option>
            </Dropdown>
          </Field>
          <Button appearance="primary" onClick={submit} disabled={busy || !subject.trim()}>
            {busy ? "Creating…" : "Create request"}
          </Button>
        </div>

        {requests.length > 0 && (
          <Table aria-label="Data subject requests" size="small">
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Subject</TableHeaderCell>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Result</TableHeaderCell>
                <TableHeaderCell />
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.subject}</TableCell>
                  <TableCell>{KIND_LABEL[r.kind] ?? r.kind}</TableCell>
                  <TableCell>
                    <Badge appearance="tint" color={STATUS_COLOR[r.status] ?? "informative"}>
                      {r.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Caption1 style={{ color: palette.inkSubtle }}>
                      {r.result?.erased_documents !== undefined
                        ? `${String(r.result.erased_documents)} erased`
                        : r.result?.document_count !== undefined
                          ? `${String(r.result.document_count)} documents`
                          : "—"}
                    </Caption1>
                  </TableCell>
                  <TableCell>
                    {r.status === "pending" && (
                      <Button
                        size="small"
                        appearance="subtle"
                        icon={<PlayRegular />}
                        onClick={() => process(r.id)}
                      >
                        Process
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
