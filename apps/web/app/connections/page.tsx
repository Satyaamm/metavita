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
  Spinner,
  Switch,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import {
  AddRegular,
  CheckmarkCircleFilled,
  DeleteRegular,
  EditRegular,
  ErrorCircleFilled,
  PlugConnectedRegular,
} from "@fluentui/react-icons";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import { ProviderLogo } from "@/components/ProviderLogo";
import type { CatalogField, CatalogProvider, ConnectionItem } from "@/lib/api";
import { useConnectionsStore } from "@/lib/stores/connections";
import { appTokens, palette, tints } from "../theme";

const STATUS: Record<string, { color: "informative" | "success" | "danger"; label: string }> = {
  untested: { color: "informative", label: "Untested" },
  ok: { color: "success", label: "Connected" },
  error: { color: "danger", label: "Error" },
};

const useStyles = makeStyles({
  group: { display: "flex", flexDirection: "column", gap: "10px", marginBottom: "24px" },
  groupHead: { display: "flex", alignItems: "baseline", gap: "8px" },
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
    background: palette.canvas,
    border: `1px solid ${appTokens.border}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  footer: { display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "4px" },
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "480px", maxHeight: "60vh", overflowY: "auto" },
});

function DynamicField({
  field,
  value,
  onChange,
}: {
  field: CatalogField;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  if (field.type === "boolean") {
    return (
      <Switch
        checked={!!value}
        label={field.label}
        onChange={(_, d) => onChange(d.checked)}
      />
    );
  }
  if (field.type === "select") {
    return (
      <Field label={field.label} required={field.required} hint={field.help || undefined}>
        <Dropdown
          value={(value as string) ?? ""}
          selectedOptions={value ? [value as string] : []}
          onOptionSelect={(_, d) => onChange(d.optionValue)}
        >
          {field.options.map((o) => (
            <Option key={o} value={o}>
              {o}
            </Option>
          ))}
        </Dropdown>
      </Field>
    );
  }
  return (
    <Field label={field.label} required={field.required} hint={field.help || undefined}>
      <Input
        type={field.type === "password" ? "password" : field.type === "number" ? "number" : "text"}
        value={(value as string) ?? ""}
        placeholder={field.placeholder}
        onChange={(_, d) => onChange(d.value)}
      />
    </Field>
  );
}

function AddConnectionDialog() {
  const styles = useStyles();
  const { catalog, create } = useConnectionsStore();
  const [open, setOpen] = useState(false);
  const [capability, setCapability] = useState<string>("");
  const [providerKey, setProviderKey] = useState<string>("");
  const [name, setName] = useState("");
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const capabilities = catalog?.capabilities ?? [];
  const providers: CatalogProvider[] =
    capabilities.find((c) => c.key === capability)?.providers ?? [];
  const provider = providers.find((p) => p.provider === providerKey) ?? null;

  function reset() {
    setCapability("");
    setProviderKey("");
    setName("");
    setValues({});
    setErr(null);
  }

  function pickProvider(p: CatalogProvider) {
    setProviderKey(p.provider);
    if (!name) setName(p.label);
    const defaults: Record<string, unknown> = {};
    for (const f of p.fields) if (f.default != null) defaults[f.name] = f.default;
    setValues(defaults);
  }

  async function submit() {
    if (!provider || !name.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      await create({ name: name.trim(), capability, provider: provider.provider, values });
      setOpen(false);
      reset();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  const capLabel = (k: string) => capabilities.find((c) => c.key === k)?.label ?? k;

  return (
    <Dialog open={open} onOpenChange={(_, d) => { setOpen(d.open); if (!d.open) reset(); }}>
      <DialogTrigger disableButtonEnhancement>
        <Button appearance="primary" icon={<AddRegular />}>
          Add connection
        </Button>
      </DialogTrigger>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>Add a connection</DialogTitle>
          <DialogContent>
            <div className={styles.form}>
              <Field label="Service type" required>
                <Dropdown
                  value={capability ? capLabel(capability) : ""}
                  selectedOptions={capability ? [capability] : []}
                  onOptionSelect={(_, d) => {
                    setCapability(d.optionValue as string);
                    setProviderKey("");
                    setValues({});
                  }}
                >
                  {capabilities.map((c) => (
                    <Option key={c.key} value={c.key} text={c.label}>
                      {c.label}
                    </Option>
                  ))}
                </Dropdown>
              </Field>

              {capability && (
                <Field label="Provider" required>
                  <Dropdown
                    value={provider?.label ?? ""}
                    selectedOptions={providerKey ? [providerKey] : []}
                    onOptionSelect={(_, d) => {
                      const p = providers.find((x) => x.provider === d.optionValue);
                      if (p) pickProvider(p);
                    }}
                  >
                    {providers.map((p) => (
                      <Option key={p.provider} value={p.provider} text={p.label}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                          <ProviderLogo provider={p.provider} label={p.label} size={18} />
                          {p.label} — {p.description}
                        </span>
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
              )}

              {provider && (
                <>
                  <Field label="Name" required>
                    <Input value={name} onChange={(_, d) => setName(d.value)} />
                  </Field>
                  {provider.fields.map((f) => (
                    <DynamicField
                      key={f.name}
                      field={f}
                      value={values[f.name]}
                      onChange={(v) => setValues((prev) => ({ ...prev, [f.name]: v }))}
                    />
                  ))}
                  {provider.docs_url && (
                    <Caption1 style={{ color: palette.inkSubtle }}>
                      <a href={provider.docs_url} target="_blank" rel="noreferrer">
                        {provider.label} docs →
                      </a>
                    </Caption1>
                  )}
                  {err && <Caption1 style={{ color: palette.danger }}>{err}</Caption1>}
                </>
              )}
            </div>
          </DialogContent>
          <DialogActions>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="secondary">Cancel</Button>
            </DialogTrigger>
            <Button appearance="primary" onClick={submit} disabled={busy || !provider || !name.trim()}>
              {busy ? "Saving…" : "Add connection"}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

function EditConnectionDialog({
  conn,
  fields,
}: {
  conn: ConnectionItem;
  fields: CatalogField[];
}) {
  const styles = useStyles();
  const update = useConnectionsStore((s) => s.update);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(conn.name);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [busy, setBusy] = useState(false);

  function start(o: boolean) {
    setOpen(o);
    if (o) {
      setName(conn.name);
      setValues({ ...conn.config }); // secrets stay blank — blank keeps current
    }
  }

  async function submit() {
    setBusy(true);
    try {
      // Only send non-empty secrets so blanks don't wipe stored values.
      const payload: Record<string, unknown> = {};
      for (const f of fields) {
        const v = values[f.name];
        if (f.secret) {
          if (v) payload[f.name] = v;
        } else if (v !== undefined) {
          payload[f.name] = v;
        }
      }
      await update(conn.id, { name: name.trim() || conn.name, values: payload });
      setOpen(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(_, d) => start(d.open)}>
      <DialogTrigger disableButtonEnhancement>
        <Button size="small" appearance="subtle" icon={<EditRegular />} aria-label="Edit connection" />
      </DialogTrigger>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>Edit {conn.provider_label}</DialogTitle>
          <DialogContent>
            <div className={styles.form}>
              <Field label="Name" required>
                <Input value={name} onChange={(_, d) => setName(d.value)} />
              </Field>
              {fields.map((f) => (
                <DynamicField
                  key={f.name}
                  field={
                    f.secret && conn.secrets_set.includes(f.name)
                      ? { ...f, placeholder: "•••• set — leave blank to keep", required: false }
                      : f
                  }
                  value={values[f.name]}
                  onChange={(v) => setValues((prev) => ({ ...prev, [f.name]: v }))}
                />
              ))}
            </div>
          </DialogContent>
          <DialogActions>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="secondary">Cancel</Button>
            </DialogTrigger>
            <Button appearance="primary" onClick={submit} disabled={busy}>
              {busy ? "Saving…" : "Save changes"}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

export default function ConnectionsPage() {
  const styles = useStyles();
  const { items, catalog, status, testing, fetch, test, remove } = useConnectionsStore();

  const providerFields = (c: ConnectionItem): CatalogField[] =>
    catalog?.capabilities
      .find((cap) => cap.key === c.capability)
      ?.providers.find((p) => p.provider === c.provider)?.fields ?? [];

  useEffect(() => {
    fetch();
  }, [fetch]);

  const byCapability = useMemo(() => {
    const groups: Record<string, typeof items> = {};
    for (const c of items) (groups[c.capability] ??= []).push(c);
    return groups;
  }, [items]);

  const capLabel = (k: string) =>
    catalog?.capabilities.find((c) => c.key === k)?.label ?? k;
  const orderedCaps = catalog?.capabilities.map((c) => c.key) ?? Object.keys(byCapability);

  return (
    <>
      <PageHeader
        title="Connections"
        description="Bring your own models, vector databases, and services. MetaVita stores no keys of its own — everything here is yours."
        actions={<AddConnectionDialog />}
      />

      {(status === "idle" || status === "loading") && <CardGridSkeleton count={6} />}

      {status === "ready" && items.length === 0 && (
        <EmptyState
          icon={<PlugConnectedRegular />}
          title="No connections yet"
          description="Add an LLM, embeddings model, vector database, or video analyzer to start building."
        />
      )}

      {status === "ready" &&
        orderedCaps
          .filter((cap) => (byCapability[cap]?.length ?? 0) > 0)
          .map((cap) => (
            <div key={cap} className={styles.group}>
              <div className={styles.groupHead}>
                <Text weight="semibold">{capLabel(cap)}</Text>
                <Caption1 style={{ color: palette.inkSubtle }}>
                  {byCapability[cap].length}
                </Caption1>
              </div>
              <div className={styles.grid}>
                {byCapability[cap].map((c) => {
                  const st = STATUS[c.status] ?? STATUS.untested;
                  return (
                    <div key={c.id} className={styles.card}>
                      <div className={styles.top}>
                        <span className={styles.icon}>
                          <ProviderLogo provider={c.provider} label={c.provider_label} size={26} />
                        </span>
                        <Badge appearance="tint" color={st.color}>
                          {c.status === "ok" && <CheckmarkCircleFilled style={{ marginRight: 4 }} />}
                          {c.status === "error" && <ErrorCircleFilled style={{ marginRight: 4 }} />}
                          {st.label}
                        </Badge>
                      </div>
                      <Text weight="semibold">{c.name}</Text>
                      <Caption1 style={{ color: palette.inkSubtle }}>{c.provider_label}</Caption1>
                      {c.status_detail && (
                        <Caption1 style={{ color: c.status === "error" ? palette.danger : palette.inkSubtle }}>
                          {c.status_detail}
                        </Caption1>
                      )}
                      <div className={styles.footer}>
                        <Button
                          size="small"
                          appearance="secondary"
                          disabled={!!testing[c.id]}
                          onClick={() => test(c.id)}
                        >
                          {testing[c.id] ? <Spinner size="tiny" /> : "Test"}
                        </Button>
                        <div style={{ display: "flex", gap: 4 }}>
                          <EditConnectionDialog conn={c} fields={providerFields(c)} />
                          <Button
                            size="small"
                            appearance="subtle"
                            icon={<DeleteRegular />}
                            aria-label="Delete connection"
                            onClick={() => remove(c.id)}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
    </>
  );
}
