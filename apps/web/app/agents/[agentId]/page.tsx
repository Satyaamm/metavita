"use client";

import {
  Button,
  Caption1,
  Checkbox,
  Dropdown,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Option,
  Spinner,
  Switch,
  Textarea,
  makeStyles,
} from "@fluentui/react-components";
import { ArrowLeftRegular, SaveRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import {
  type AgentConnectionSlots,
  type AgentItem,
  type ConnectionItem,
  api,
} from "@/lib/api";
import { useIndexesStore } from "@/lib/stores/knowledge";
import { appTokens, palette } from "../../theme";

const PROVIDERS = ["anthropic", "openai", "ollama"];

// Builder connection slots: which BYO Connection fills each capability at run time.
const SLOTS: { key: keyof AgentConnectionSlots; label: string; capability: string }[] = [
  { key: "llm_connection_id", label: "LLM connection", capability: "llm" },
  { key: "embedding_connection_id", label: "Embeddings connection", capability: "embeddings" },
  {
    key: "vector_store_connection_id",
    label: "Vector store connection",
    capability: "vector_store",
  },
];

const EMPTY_SLOTS: AgentConnectionSlots = {
  llm_connection_id: null,
  embedding_connection_id: null,
  vector_store_connection_id: null,
};
const TOOLS = [
  { key: "retriever", label: "Retriever (search attached index)" },
  { key: "web_search", label: "Web search" },
  { key: "http_request", label: "HTTP request" },
  { key: "code_exec", label: "Code execution" },
];

const useStyles = makeStyles({
  back: { display: "inline-flex", alignItems: "center", gap: "6px", color: palette.inkSubtle, textDecoration: "none" },
  grid: { display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "20px", alignItems: "start", "@media (max-width: 900px)": { gridTemplateColumns: "1fr" } },
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
  tools: { display: "flex", flexDirection: "column", gap: "6px" },
  bar: { display: "flex", alignItems: "center", gap: "12px" },
});

export default function AgentBuilderPage() {
  const styles = useStyles();
  const { agentId } = useParams<{ agentId: string }>();
  const { items: indexes, fetch: fetchIndexes } = useIndexesStore();

  const [agent, setAgent] = useState<AgentItem | null>(null);
  const [slots, setSlots] = useState<AgentConnectionSlots>(EMPTY_SLOTS);
  const [connections, setConnections] = useState<Record<string, ConnectionItem[]>>({});
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getAgent(agentId)
      .then((a) => {
        setAgent(a);
        // Slot ids ride on the agent payload (typed separately to keep AgentItem stable).
        const withSlots = a as AgentItem & Partial<AgentConnectionSlots>;
        setSlots({
          llm_connection_id: withSlots.llm_connection_id ?? null,
          embedding_connection_id: withSlots.embedding_connection_id ?? null,
          vector_store_connection_id: withSlots.vector_store_connection_id ?? null,
        });
      })
      .catch((e) => setError(String(e)));
    fetchIndexes();
    // Load the workspace's connections per capability for the slot pickers.
    Promise.all(
      SLOTS.map((s) =>
        api
          .listConnections({ capability: s.capability })
          .then((r) => [s.capability, r.items] as const)
          .catch(() => [s.capability, [] as ConnectionItem[]] as const),
      ),
    ).then((pairs) => setConnections(Object.fromEntries(pairs)));
  }, [agentId, fetchIndexes]);

  function patch(p: Partial<AgentItem>) {
    setAgent((a) => (a ? { ...a, ...p } : a));
  }

  function toggleTool(key: string, on: boolean) {
    if (!agent) return;
    const tools = on ? [...agent.tools, key] : agent.tools.filter((t) => t !== key);
    patch({ tools });
  }

  async function save() {
    if (!agent) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateAgent(agentId, {
        name: agent.name,
        system_prompt: agent.system_prompt,
        provider: agent.provider,
        model: agent.model,
        tools: agent.tools,
        index_id: agent.index_id,
        memory: agent.memory,
        status: agent.status,
        // Connection slots — sent alongside the core fields (see api note on AgentItem).
        ...slots,
      } as Partial<Omit<AgentItem, "id" | "created_at" | "updated_at">>);
      setAgent(updated);
      setSavedAt(new Date(updated.updated_at ?? Date.now()).toLocaleTimeString());
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Link href="/agents" className={styles.back}>
        <ArrowLeftRegular /> Agents
      </Link>

      <PageHeader
        title={agent?.name ?? "Agent"}
        description="Configure the agent's prompt, model, tools, and attached knowledge."
        actions={
          <div className={styles.bar}>
            {savedAt && <Caption1 style={{ color: palette.inkSubtle }}>saved {savedAt}</Caption1>}
            <Button appearance="primary" icon={<SaveRegular />} onClick={save} disabled={saving || !agent}>
              Save
            </Button>
            {saving && <Spinner size="tiny" />}
          </div>
        }
      />

      {error && (
        <MessageBar intent="error">
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}

      {!agent && <Spinner label="Loading agent…" />}

      {agent && (
        <div className={styles.grid}>
          <div className={styles.panel}>
            <Field label="Name">
              <Input value={agent.name} onChange={(_, d) => patch({ name: d.value })} />
            </Field>
            <Field label="System prompt" hint="Instructions that define the agent's behavior.">
              <Textarea
                value={agent.system_prompt ?? ""}
                onChange={(_, d) => patch({ system_prompt: d.value })}
                placeholder="You are a helpful support assistant. Answer only from the attached knowledge…"
                resize="vertical"
                rows={8}
              />
            </Field>
          </div>

          <div className={styles.panel}>
            <Field label="Provider">
              <Dropdown
                value={agent.provider}
                selectedOptions={[agent.provider]}
                onOptionSelect={(_, d) => patch({ provider: d.optionValue as string })}
              >
                {PROVIDERS.map((p) => (
                  <Option key={p} value={p}>
                    {p}
                  </Option>
                ))}
              </Dropdown>
            </Field>
            <Field label="Model">
              <Input value={agent.model} onChange={(_, d) => patch({ model: d.value })} />
            </Field>
            <Field label="Attached index">
              <Dropdown
                value={indexes.find((i) => i.id === agent.index_id)?.name ?? "None"}
                selectedOptions={[agent.index_id ?? "none"]}
                onOptionSelect={(_, d) =>
                  patch({ index_id: d.optionValue === "none" ? null : (d.optionValue as string) })
                }
              >
                <Option value="none">None</Option>
                {indexes.map((i) => (
                  <Option key={i.id} value={i.id}>
                    {i.name}
                  </Option>
                ))}
              </Dropdown>
            </Field>
            {SLOTS.map((s) => {
              const opts = connections[s.capability] ?? [];
              const selected = slots[s.key];
              const current = opts.find((c) => c.id === selected);
              return (
                <Field
                  key={s.key}
                  label={s.label}
                  hint="Pick a connection, or use the workspace default."
                >
                  <Dropdown
                    value={current ? `${current.name} (${current.provider_label})` : "Workspace default"}
                    selectedOptions={[selected ?? "default"]}
                    onOptionSelect={(_, d) =>
                      setSlots((prev) => ({
                        ...prev,
                        [s.key]: d.optionValue === "default" ? null : (d.optionValue as string),
                      }))
                    }
                  >
                    <Option value="default">Workspace default</Option>
                    {opts.map((c) => (
                      <Option key={c.id} value={c.id} text={`${c.name} (${c.provider_label})`}>
                        {c.name} ({c.provider_label})
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
              );
            })}
            <Field label="Tools">
              <div className={styles.tools}>
                {TOOLS.map((t) => (
                  <Checkbox
                    key={t.key}
                    label={t.label}
                    checked={agent.tools.includes(t.key)}
                    onChange={(_, d) => toggleTool(t.key, Boolean(d.checked))}
                  />
                ))}
              </div>
            </Field>
            <Switch
              label="Persistent memory"
              checked={agent.memory}
              onChange={(_, d) => patch({ memory: d.checked })}
            />
          </div>
        </div>
      )}
    </>
  );
}
