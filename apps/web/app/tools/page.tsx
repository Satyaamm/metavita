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
  Dropdown,
  Field,
  Input,
  Option,
  Switch,
  Text,
  Textarea,
  makeStyles,
} from "@fluentui/react-components";
import { AddRegular, DeleteRegular, ToolboxRegular } from "@fluentui/react-icons";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import type { ToolKind } from "@/lib/api";
import { useToolsStore } from "@/lib/stores/tools";
import { appTokens, palette, tints } from "../theme";

const KINDS: { value: ToolKind; label: string; hint: string }[] = [
  { value: "http", label: "HTTP request", hint: "Call an external REST endpoint" },
  { value: "retriever", label: "Retriever", hint: "Search an index as a tool" },
  { value: "code", label: "Code execution", hint: "Run sandboxed code" },
  { value: "mcp", label: "MCP tool", hint: "A tool exposed by an MCP server" },
];

const KIND_COLOR: Record<ToolKind, "brand" | "informative" | "success" | "warning"> = {
  http: "brand",
  retriever: "informative",
  code: "success",
  mcp: "warning",
};

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
  footer: { display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "4px" },
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "480px" },
  mono: { fontFamily: "var(--fontFamilyMonospace, monospace)" },
});

function defaultConfig(kind: ToolKind): string {
  switch (kind) {
    case "http":
      return JSON.stringify({ url: "https://api.example.com/search", method: "GET" }, null, 2);
    case "retriever":
      return JSON.stringify({ index_id: "", k: 5 }, null, 2);
    case "code":
      return JSON.stringify({ language: "python", timeout_s: 10 }, null, 2);
    case "mcp":
      return JSON.stringify({ server: "my-server", tool: "search" }, null, 2);
  }
}

export default function ToolsPage() {
  const styles = useStyles();
  const { items, status, fetch, create, toggle, remove } = useToolsStore();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [kind, setKind] = useState<ToolKind>("http");
  const [description, setDescription] = useState("");
  const [config, setConfig] = useState(defaultConfig("http"));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch();
  }, [fetch]);

  function pickKind(k: ToolKind) {
    setKind(k);
    setConfig(defaultConfig(k));
  }

  async function submit() {
    if (!name.trim()) return;
    let parsed: Record<string, unknown> = {};
    try {
      parsed = config.trim() ? JSON.parse(config) : {};
    } catch {
      setErr("Config must be valid JSON.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await create({ name: name.trim(), kind, description, config: parsed, input_schema: {} });
      setOpen(false);
      setName("");
      setDescription("");
      pickKind("http");
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  const kindLabel = (k: ToolKind) => KINDS.find((x) => x.value === k)?.label ?? k;

  return (
    <>
      <PageHeader
        title="Tools"
        description="The tools your agents can call — retriever, HTTP, code execution, and MCP tools."
        actions={
          <Dialog open={open} onOpenChange={(_, d) => setOpen(d.open)}>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="primary" icon={<AddRegular />}>
                New tool
              </Button>
            </DialogTrigger>
            <DialogSurface>
              <DialogBody>
                <DialogTitle>Register a tool</DialogTitle>
                <DialogContent>
                  <div className={styles.form}>
                    <Field label="Name" required hint="Exposed to the model — use snake_case.">
                      <Input value={name} onChange={(_, d) => setName(d.value)} placeholder="web_search" />
                    </Field>
                    <Field label="Kind">
                      <Dropdown
                        value={kindLabel(kind)}
                        selectedOptions={[kind]}
                        onOptionSelect={(_, d) => pickKind(d.optionValue as ToolKind)}
                      >
                        {KINDS.map((k) => (
                          <Option key={k.value} value={k.value} text={k.label}>
                            {k.label} — {k.hint}
                          </Option>
                        ))}
                      </Dropdown>
                    </Field>
                    <Field label="Description" hint="Tells the model when to reach for this tool.">
                      <Textarea
                        value={description}
                        onChange={(_, d) => setDescription(d.value)}
                        rows={2}
                        placeholder="Search the public web for recent information."
                      />
                    </Field>
                    <Field
                      label="Config (JSON)"
                      validationState={err ? "error" : "none"}
                      validationMessage={err ?? undefined}
                    >
                      <Textarea
                        className={styles.mono}
                        value={config}
                        onChange={(_, d) => setConfig(d.value)}
                        rows={6}
                      />
                    </Field>
                  </div>
                </DialogContent>
                <DialogActions>
                  <DialogTrigger disableButtonEnhancement>
                    <Button appearance="secondary">Cancel</Button>
                  </DialogTrigger>
                  <Button appearance="primary" onClick={submit} disabled={busy || !name.trim()}>
                    {busy ? "Saving…" : "Register"}
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
          icon={<ToolboxRegular />}
          title="No custom tools yet"
          description="Register custom or MCP tools here to make them available to agents."
        />
      )}

      {status === "ready" && items.length > 0 && (
        <div className={styles.grid}>
          {items.map((t) => (
            <div key={t.id} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.icon}>
                  <ToolboxRegular />
                </span>
                <Badge appearance="tint" color={KIND_COLOR[t.kind]}>
                  {kindLabel(t.kind)}
                </Badge>
              </div>
              <Text weight="semibold" className={styles.mono}>
                {t.name}
              </Text>
              <Caption1 style={{ color: palette.inkSubtle, minHeight: 32 }}>
                {t.description || "No description."}
              </Caption1>
              <div className={styles.footer}>
                <Switch
                  checked={t.enabled}
                  label={t.enabled ? "Enabled" : "Disabled"}
                  onChange={(_, d) => toggle(t.id, d.checked)}
                />
                <Button
                  appearance="subtle"
                  size="small"
                  icon={<DeleteRegular />}
                  aria-label="Delete tool"
                  onClick={() => remove(t.id)}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
