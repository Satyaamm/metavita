"use client";

import "@xyflow/react/dist/style.css";

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
  Dropdown,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Option,
  Spinner,
  TabList,
  Tab,
  Text,
  Textarea,
  makeStyles,
} from "@fluentui/react-components";
import { ArrowLeftRegular, PlayRegular, SaveRegular } from "@fluentui/react-icons";
import {
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
} from "@xyflow/react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { type ConnectionItem, type PipelineItem, api } from "@/lib/api";
import { makeNode, validateGraph } from "@/lib/pipeline/graph";
import { CATEGORY_TINT, NODE_TYPES, PALETTE } from "@/lib/pipeline/nodes";
import { appTokens, palette } from "../../app/theme";

const useStyles = makeStyles({
  topbar: { display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" },
  back: { display: "inline-flex", alignItems: "center", gap: "6px", color: palette.inkSubtle, textDecoration: "none" },
  spacer: { flex: 1 },
  layout: { display: "grid", gridTemplateColumns: "210px 1fr 240px", gap: "0", height: "70vh", border: `1px solid ${appTokens.border}`, borderRadius: appTokens.radiusCard, overflow: "hidden", backgroundColor: appTokens.surfaceBg },
  palette: { borderRight: `1px solid ${appTokens.border}`, padding: "14px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "14px" },
  palGroup: { display: "flex", flexDirection: "column", gap: "6px" },
  palLabel: { color: palette.inkSubtle, textTransform: "uppercase", letterSpacing: "0.05em", fontSize: "11px" },
  palItem: { display: "flex", alignItems: "center", gap: "8px", padding: "7px 10px", borderRadius: "8px", border: `1px solid ${appTokens.border}`, background: "#fff", cursor: "pointer", fontSize: "13px", fontWeight: 500, textAlign: "left", ":hover": { border: `1px solid ${palette.brandPrimary}` } },
  swatch: { width: "10px", height: "10px", borderRadius: "3px", flexShrink: 0 },
  canvas: { position: "relative" },
  inspector: { borderLeft: `1px solid ${appTokens.border}`, padding: "16px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "12px" },
  code: { height: "70vh", overflow: "auto", margin: 0, padding: "16px", borderRadius: appTokens.radiusCard, border: `1px solid ${appTokens.border}`, background: "#0E1020", color: "#D7DAF0", fontFamily: "ui-monospace, Menlo, monospace", fontSize: "12.5px" },
});

function MetaNode({ data, type, selected }: NodeProps) {
  const def = NODE_TYPES[type as string];
  const tint = def ? CATEGORY_TINT[def.category] : "#E6E9EB";
  return (
    <div
      style={{
        borderRadius: 10,
        border: `1.5px solid ${selected ? palette.brandPrimary : appTokens.border}`,
        background: "#fff",
        minWidth: 150,
        boxShadow: appTokens.shadowCard,
      }}
    >
      <Handle type="target" position={Position.Left} />
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 12px" }}>
        <span style={{ width: 10, height: 10, borderRadius: 3, background: tint }} />
        <span style={{ fontWeight: 600, fontSize: 13 }}>
          {(data?.label as string) ?? (type as string)}
        </span>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const NODE_COMPONENTS = Object.fromEntries(Object.keys(NODE_TYPES).map((t) => [t, MetaNode]));

// Which Connection capability each node type pins via `data.connection_id`.
// Mirrors the pipeline run route, which resolves providers from these slots.
const NODE_CAPABILITY: Record<string, string> = {
  llm: "llm",
  embed: "embeddings",
  retrieve: "vector_store",
};

export function PipelineBuilder({ pipelineId, tab }: { pipelineId: string; tab: string }) {
  const styles = useStyles();
  const [pipeline, setPipeline] = useState<PipelineItem | null>(null);
  const [name, setName] = useState("");
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [connections, setConnections] = useState<Record<string, ConnectionItem[]>>({});
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const [runOpen, setRunOpen] = useState(false);
  const [runQ, setRunQ] = useState("");
  const [running, setRunning] = useState(false);
  const [runRes, setRunRes] = useState<{ runId: string; answer: string } | null>(null);

  async function run() {
    if (!runQ.trim()) return;
    setRunning(true);
    setRunRes(null);
    try {
      const r = await api.runPipeline(pipelineId, { question: runQ });
      setRunRes({ runId: r.run_id, answer: r.answer });
    } catch (e) {
      setRunRes({ runId: "", answer: `Error: ${String(e)}` });
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => {
    api.getPipeline(pipelineId).then((p) => {
      setPipeline(p);
      setName(p.name);
      setNodes((p.graph?.nodes ?? []) as Node[]);
      setEdges((p.graph?.edges ?? []) as Edge[]);
    });
    // Load connections per capability for the node-level slot pickers.
    const caps = Array.from(new Set(Object.values(NODE_CAPABILITY)));
    Promise.all(
      caps.map((cap) =>
        api
          .listConnections({ capability: cap })
          .then((r) => [cap, r.items] as const)
          .catch(() => [cap, [] as ConnectionItem[]] as const),
      ),
    ).then((pairs) => setConnections(Object.fromEntries(pairs)));
  }, [pipelineId]);

  const onNodesChange = useCallback((c: Parameters<typeof applyNodeChanges>[0]) => {
    setNodes((nds) => applyNodeChanges(c, nds));
  }, []);
  const onEdgesChange = useCallback((c: Parameters<typeof applyEdgeChanges>[0]) => {
    setEdges((eds) => applyEdgeChanges(c, eds));
  }, []);
  const onConnect = useCallback((c: Connection) => setEdges((eds) => addEdge(c, eds)), []);

  function addNode(type: string) {
    const i = nodes.length;
    const node = makeNode(type, { x: 120 + (i % 4) * 190, y: 70 + Math.floor(i / 4) * 120 });
    setNodes((nds) => [...nds, node as Node]);
  }

  const selected = nodes.find((n) => n.id === selectedId) ?? null;

  function setSelectedLabel(label: string) {
    setNodes((nds) =>
      nds.map((n) => (n.id === selectedId ? { ...n, data: { ...n.data, label } } : n)),
    );
  }

  function setSelectedConnection(connectionId: string | null) {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedId ? { ...n, data: { ...n.data, connection_id: connectionId } } : n,
      ),
    );
  }

  async function save() {
    const graph = {
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type as string,
        position: n.position,
        data: n.data as Record<string, unknown>,
      })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
    };
    const issues = validateGraph(graph);
    setErrors(issues);
    if (issues.length) return;
    setSaving(true);
    try {
      const p = await api.updatePipeline(pipelineId, { name, graph });
      setSavedAt(new Date(p.updated_at ?? Date.now()).toLocaleTimeString());
    } catch (e) {
      setErrors([String(e)]);
    } finally {
      setSaving(false);
    }
  }

  const graphForCode = useMemo(
    () => ({
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
    }),
    [nodes, edges],
  );

  return (
    <>
      <Link href="/pipelines" className={styles.back}>
        <ArrowLeftRegular /> Pipelines
      </Link>

      <div className={styles.topbar}>
        <Input value={name} onChange={(_, d) => setName(d.value)} style={{ minWidth: 240, fontWeight: 600 }} />
        <TabList selectedValue={tab}>
          <Tab value="canvas">
            <Link href={`/pipelines/${pipelineId}?tab=canvas`} style={{ textDecoration: "none", color: "inherit" }}>
              Canvas
            </Link>
          </Tab>
          <Tab value="code">
            <Link href={`/pipelines/${pipelineId}?tab=code`} style={{ textDecoration: "none", color: "inherit" }}>
              Code
            </Link>
          </Tab>
        </TabList>
        <div className={styles.spacer} />
        {savedAt && <Caption1 style={{ color: palette.inkSubtle }}>saved {savedAt}</Caption1>}

        <Dialog open={runOpen} onOpenChange={(_, d) => setRunOpen(d.open)}>
          <DialogTrigger disableButtonEnhancement>
            <Button icon={<PlayRegular />}>Run</Button>
          </DialogTrigger>
          <DialogSurface>
            <DialogBody>
              <DialogTitle>Run pipeline</DialogTitle>
              <DialogContent>
                <Field label="Question" hint="Runs embed → retrieve → generate and records a trace.">
                  <Textarea
                    value={runQ}
                    onChange={(_, d) => setRunQ(d.value)}
                    placeholder="What are the key findings?"
                    resize="vertical"
                  />
                </Field>
                {runRes && (
                  <MessageBar intent={runRes.runId ? "success" : "error"} style={{ marginTop: 12 }}>
                    <MessageBarBody>
                      {runRes.answer}
                      {runRes.runId && (
                        <>
                          {" "}
                          <Link href={`/traces/${runRes.runId}`}>View trace →</Link>
                        </>
                      )}
                    </MessageBarBody>
                  </MessageBar>
                )}
              </DialogContent>
              <DialogActions>
                <Button appearance="primary" icon={<PlayRegular />} onClick={run} disabled={running || !runQ}>
                  {running ? "Running…" : "Run"}
                </Button>
                {running && <Spinner size="tiny" />}
              </DialogActions>
            </DialogBody>
          </DialogSurface>
        </Dialog>

        <Button appearance="primary" icon={<SaveRegular />} onClick={save} disabled={saving}>
          Save
        </Button>
        {saving && <Spinner size="tiny" />}
      </div>

      {errors.length > 0 && (
        <MessageBar intent="error">
          <MessageBarBody>{errors.join(" · ")}</MessageBarBody>
        </MessageBar>
      )}

      {!pipeline && <Spinner label="Loading builder…" />}

      {pipeline && tab === "code" && (
        <pre className={styles.code}>{JSON.stringify(graphForCode, null, 2)}</pre>
      )}

      {pipeline && tab !== "code" && (
        <div className={styles.layout}>
          {/* Palette */}
          <div className={styles.palette}>
            {PALETTE.map((group) => (
              <div key={group.category} className={styles.palGroup}>
                <Caption1 className={styles.palLabel}>{group.label}</Caption1>
                {group.types.map((t) => (
                  <button key={t} type="button" className={styles.palItem} onClick={() => addNode(t)}>
                    <span className={styles.swatch} style={{ background: CATEGORY_TINT[NODE_TYPES[t].category] }} />
                    {NODE_TYPES[t].label}
                  </button>
                ))}
              </div>
            ))}
          </div>

          {/* Canvas */}
          <div className={styles.canvas}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={NODE_COMPONENTS}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, n) => setSelectedId(n.id)}
              onPaneClick={() => setSelectedId(null)}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#E6E8EC" gap={18} />
              <Controls showInteractive={false} />
              <MiniMap pannable zoomable />
            </ReactFlow>
          </div>

          {/* Inspector */}
          <div className={styles.inspector}>
            {selected ? (
              <>
                <Text weight="semibold">{NODE_TYPES[selected.type as string]?.label ?? selected.type}</Text>
                <Caption1 style={{ color: palette.inkSubtle }}>
                  {NODE_TYPES[selected.type as string]?.description}
                </Caption1>
                <Field label="Label">
                  <Input
                    value={(selected.data?.label as string) ?? ""}
                    onChange={(_, d) => setSelectedLabel(d.value)}
                  />
                </Field>
                {NODE_CAPABILITY[selected.type as string] &&
                  (() => {
                    const cap = NODE_CAPABILITY[selected.type as string];
                    const opts = connections[cap] ?? [];
                    const selectedConn = (selected.data?.connection_id as string | null) ?? null;
                    const current = opts.find((c) => c.id === selectedConn);
                    return (
                      <Field
                        label="Connection"
                        hint="Pick a connection for this step, or use the workspace default."
                      >
                        <Dropdown
                          value={
                            current
                              ? `${current.name} (${current.provider_label})`
                              : "Workspace default"
                          }
                          selectedOptions={[selectedConn ?? "default"]}
                          onOptionSelect={(_, d) =>
                            setSelectedConnection(
                              d.optionValue === "default" ? null : (d.optionValue as string),
                            )
                          }
                        >
                          <Option value="default">Workspace default</Option>
                          {opts.map((c) => (
                            <Option
                              key={c.id}
                              value={c.id}
                              text={`${c.name} (${c.provider_label})`}
                            >
                              {c.name} ({c.provider_label})
                            </Option>
                          ))}
                        </Dropdown>
                      </Field>
                    );
                  })()}
              </>
            ) : (
              <Caption1 style={{ color: palette.inkSubtle }}>
                Click a node from the palette to add it, then connect nodes by dragging between handles.
                Select a node to configure it.
              </Caption1>
            )}
          </div>
        </div>
      )}
    </>
  );
}
