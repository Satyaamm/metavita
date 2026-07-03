"use client";

import {
  Avatar,
  Badge,
  Button,
  Caption1,
  Combobox,
  Option,
  Spinner,
  Text,
  Textarea,
  makeStyles,
} from "@fluentui/react-components";
import { BeakerRegular, SendRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { ConnectionGuard } from "@/components/ConnectionGuard";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { type Citation, api } from "@/lib/api";
import { drainSseFrames } from "@/lib/sse";
import { useAgentsStore, usePipelinesStore } from "@/lib/stores/build";
import { appTokens, palette, tints } from "../theme";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  runId?: string;
}

const useStyles = makeStyles({
  grid: { display: "grid", gridTemplateColumns: "1.7fr 1fr", gap: "20px", alignItems: "stretch", height: "calc(100vh - 200px)", "@media (max-width: 980px)": { gridTemplateColumns: "1fr" } },
  chat: { display: "flex", flexDirection: "column", backgroundColor: appTokens.surfaceBg, border: `1px solid ${appTokens.border}`, borderRadius: appTokens.radiusCard, boxShadow: appTokens.shadowCard, overflow: "hidden" },
  thread: { flex: 1, overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: "14px" },
  msg: { display: "flex", gap: "10px", maxWidth: "85%" },
  msgUser: { alignSelf: "flex-end", flexDirection: "row-reverse" },
  bubble: { padding: "10px 14px", borderRadius: "12px", whiteSpace: "pre-wrap", fontSize: "14px", lineHeight: 1.5 },
  bubbleUser: { backgroundColor: palette.brandPrimary, color: "#fff" },
  bubbleAsst: { backgroundColor: palette.canvas, border: `1px solid ${appTokens.border}`, color: palette.ink },
  composer: { borderTop: `1px solid ${appTokens.border}`, padding: "12px", display: "flex", gap: "10px", alignItems: "flex-end" },
  inspector: { backgroundColor: appTokens.surfaceBg, border: `1px solid ${appTokens.border}`, borderRadius: appTokens.radiusCard, boxShadow: appTokens.shadowCard, padding: "18px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "12px" },
  cite: { borderLeft: `3px solid ${palette.brandPrimary}`, paddingLeft: "10px", display: "flex", flexDirection: "column", gap: "2px" },
  pill: { background: `linear-gradient(135deg, ${tints.lilac}, ${tints.sky})`, color: palette.brandPrimary, borderRadius: "999px", padding: "1px 8px", fontSize: "11px", fontWeight: 700, alignSelf: "flex-start" },
});

function uid() {
  return crypto.randomUUID();
}

function PlaygroundInner() {
  const styles = useStyles();
  const router = useRouter();
  const params = useSearchParams();
  const target = params.get("target") ?? "default";

  const { items: pipelines, fetch: fetchPipelines } = usePipelinesStore();
  const { items: agents, fetch: fetchAgents } = useAgentsStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [pickerQuery, setPickerQuery] = useState("");
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPipelines();
    fetchAgents();
  }, [fetchPipelines, fetchAgents]);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
  }, [messages]);

  const agentId = target.startsWith("agent:") ? target.slice(6) : null;
  const targetName = agentId
    ? (agents.find((a) => a.id === agentId)?.name ?? "Agent")
    : target === "default"
      ? "Default knowledge base"
      : (pipelines.find((p) => p.id === target)?.name ?? "Pipeline");

  function update(id: string, patch: Partial<Message>) {
    setMessages((ms) => ms.map((m) => (m.id === id ? { ...m, ...patch } : m)));
  }

  async function send() {
    const q = input.trim();
    if (!q || busy) return;
    setInput("");
    setMessages((ms) => [...ms, { id: uid(), role: "user", content: q }]);
    const aid = uid();
    setMessages((ms) => [...ms, { id: aid, role: "assistant", content: "" }]);
    setBusy(true);
    try {
      if (agentId) {
        const r = await api.runAgent(agentId, { message: q });
        update(aid, { content: r.answer, runId: r.run_id });
      } else if (target === "default") {
        const res = await fetch("/api/query/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q, k: 5 }),
        });
        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let answer = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const { events, rest } = drainSseFrames(buffer);
          buffer = rest;
          for (const ev of events) {
            if (ev.event === "citations") update(aid, { citations: JSON.parse(ev.data) });
            else if (ev.event === "token") {
              answer += ev.data;
              update(aid, { content: answer });
            }
          }
        }
      } else {
        const r = await api.runPipeline(target, { question: q });
        update(aid, { content: r.answer, citations: r.citations, runId: r.run_id });
      }
    } catch (e) {
      update(aid, { content: `Error: ${String(e)}` });
    } finally {
      setBusy(false);
    }
  }

  const lastCited = [...messages].reverse().find((m) => m.role === "assistant" && m.citations?.length);

  return (
    <>
      <PageHeader
        title="Playground"
        description="Chat against a pipeline or your knowledge base, with the retrieved context alongside."
        actions={
          <Combobox
            placeholder={`Search… (${targetName})`}
            value={pickerQuery}
            selectedOptions={[target]}
            onChange={(e) => setPickerQuery(e.target.value)}
            onOptionSelect={(_, d) => {
              router.replace(`/playground?target=${d.optionValue}`);
              setPickerQuery("");
            }}
            style={{ minWidth: 240 }}
          >
            {(() => {
              const q = pickerQuery.trim().toLowerCase();
              const opts = [
                { value: "default", label: "Default knowledge base", name: "Default knowledge base" },
                ...pipelines.map((p) => ({ value: p.id, label: `Pipeline · ${p.name}`, name: p.name })),
                ...agents.map((a) => ({ value: `agent:${a.id}`, label: `Agent · ${a.name}`, name: a.name })),
              ].filter((o) => !q || o.label.toLowerCase().includes(q));
              return opts.length ? (
                opts.map((o) => (
                  <Option key={o.value} value={o.value} text={o.name}>
                    {o.label}
                  </Option>
                ))
              ) : (
                <Option value="" disabled text="none">
                  No matches
                </Option>
              );
            })()}
          </Combobox>
        }
      />

      <ConnectionGuard need={["llm", "embeddings"]} action="chat and query your knowledge" />

      <div className={styles.grid}>
        <div className={styles.chat}>
          <div className={styles.thread} ref={threadRef}>
            {messages.length === 0 && (
              <EmptyState
                icon={<BeakerRegular />}
                title={`Ask ${targetName}`}
                description="Type a question below. The answer's retrieved context appears in the inspector."
              />
            )}
            {messages.map((m) => (
              <div
                key={m.id}
                className={`${styles.msg} ${m.role === "user" ? styles.msgUser : ""}`}
              >
                <Avatar
                  size={28}
                  name={m.role === "user" ? "You" : "MetaVita"}
                  color={m.role === "user" ? "brand" : "neutral"}
                />
                <div
                  className={`${styles.bubble} ${m.role === "user" ? styles.bubbleUser : styles.bubbleAsst}`}
                >
                  {m.content || (busy ? "…" : "")}
                  {m.runId && (
                    <div style={{ marginTop: 6 }}>
                      <Link href={`/traces/${m.runId}`} style={{ fontSize: 12 }}>
                        View trace →
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className={styles.composer}>
            <Textarea
              style={{ flex: 1 }}
              value={input}
              onChange={(_, d) => setInput(d.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder={`Message ${targetName}…`}
            />
            <Button appearance="primary" icon={<SendRegular />} onClick={send} disabled={busy}>
              Send
            </Button>
            {busy && <Spinner size="tiny" />}
          </div>
        </div>

        <div className={styles.inspector}>
          <Text weight="semibold">Retrieval inspector</Text>
          {!lastCited && (
            <Caption1 style={{ color: palette.inkSubtle }}>
              The passages used to ground each answer will show up here.
            </Caption1>
          )}
          {lastCited?.citations?.map((c) => (
            <div key={c.marker} className={styles.cite}>
              <span className={styles.pill}>[{c.marker}]</span>
              <Caption1 style={{ color: palette.ink }}>{c.snippet}</Caption1>
              {c.document_id && (
                <Link href={`/knowledge/documents/${c.document_id}`} style={{ fontSize: 12 }}>
                  Open document →
                </Link>
              )}
            </div>
          ))}
          {lastCited?.runId && (
            <Badge appearance="tint" color="brand" style={{ alignSelf: "flex-start" }}>
              <Link href={`/traces/${lastCited.runId}`} style={{ color: "inherit", textDecoration: "none" }}>
                View full trace
              </Link>
            </Badge>
          )}
        </div>
      </div>
    </>
  );
}

export default function PlaygroundPage() {
  return (
    <Suspense fallback={<Spinner label="Loading playground…" />}>
      <PlaygroundInner />
    </Suspense>
  );
}
