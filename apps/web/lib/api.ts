/**
 * Typed client for the MetaVita FastAPI gateway (proxied at /api).
 * Single place that knows the wire shapes — pages consume `api.*`.
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

const BASE = "/api";
const TOKEN_KEY = "metavita_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function qs(params: Record<string, string | number | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

// --- wire types ---
export type Modality = "text" | "image" | "audio" | "video";
export type SourceType = "upload" | "web" | "connector";

export interface DataSource {
  id: string;
  name: string;
  type: SourceType;
  connector: string | null;
  modality: Modality;
  status: string;
  document_count: number | null;
  created_at: string | null;
}

export interface DocumentItem {
  id: string;
  filename: string;
  content_type: string | null;
  status: string;
  source_id: string | null;
  index_id: string | null;
  chunk_count: number | null;
  created_at: string | null;
}

export interface ChunkItem {
  chunk_index: number;
  text: string;
  meta: Record<string, unknown>;
}

export interface IndexItem {
  id: string;
  name: string;
  modality: Modality;
  embedding_provider: string;
  embedding_model: string;
  embedding_dim: number;
  chunk_size: number;
  overlap: number;
  created_at: string | null;
}

export interface IngestResult {
  document_id: string;
  filename: string;
  chunks: number;
  status: string;
}

export interface AnalyticsTotals {
  runs: number;
  succeeded: number;
  tokens_in: number;
  tokens_out: number;
  avg_latency_ms: number | null;
  est_cost_usd: number | null;
}

export interface Analytics {
  totals: AnalyticsTotals;
  by_kind: Record<string, number>;
  daily: { date: string; runs: number }[];
}

export interface OverviewStats {
  documents: number;
  chunks: number;
  sources: number;
  indexes: number;
}

export interface AuditEvent {
  id: string;
  action: string;
  actor: string;
  resource_type: string | null;
  resource_id: string | null;
  detail: Record<string, unknown>;
  created_at: string | null;
}

export interface Citation {
  marker: number;
  document_id: string | null;
  chunk_index: number | null;
  snippet: string;
}

export type NotificationSeverity = "info" | "success" | "warning" | "error";

export interface NotificationItem {
  id: string;
  action: string;
  title: string;
  detail: string;
  severity: NotificationSeverity;
  link: string | null;
  read: boolean;
  created_at: string | null;
}

export interface NotificationsResponse {
  items: NotificationItem[];
  unread: number;
}

export interface PipelineGraphShape {
  nodes: Array<{ id: string; type: string; position: { x: number; y: number }; data: Record<string, unknown> }>;
  edges: Array<{ id: string; source: string; target: string }>;
}

export interface PipelineItem {
  id: string;
  name: string;
  graph: PipelineGraphShape;
  status: string;
  version: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface SpanItem {
  seq: number;
  name: string;
  node_type: string | null;
  status: string;
  latency_ms: number | null;
  detail: Record<string, unknown>;
}

export interface RunItem {
  id: string;
  pipeline_id: string | null;
  kind: string;
  status: string;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  spans?: SpanItem[];
  latency_ms: number | null;
  tokens_in: number;
  tokens_out: number;
  created_at: string | null;
  finished_at: string | null;
}

export interface RunResult {
  run_id: string;
  status: string;
  answer: string;
  citations: Citation[];
}

export interface DeploymentItem {
  id: string;
  name: string;
  target_type: "pipeline" | "agent";
  target_id: string;
  status: string;
  key_prefix: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface DeploymentCreated extends DeploymentItem {
  api_key: string;
}

export interface AgentItem {
  id: string;
  name: string;
  system_prompt: string | null;
  provider: string;
  model: string;
  tools: string[];
  index_id: string | null;
  memory: boolean;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface EvalQA {
  question: string;
  expected?: string | null;
}

export interface EvalDatasetItem {
  id: string;
  name: string;
  items: EvalQA[];
  item_count: number;
  created_at: string | null;
}

export interface EvalScore {
  grounded: boolean;
  has_citations: boolean;
  keyword_overlap: number | null;
}

export interface EvalResult {
  question: string;
  expected: string | null;
  answer: string;
  score: EvalScore;
  latency_ms: number;
}

export interface EvalSummary {
  count: number;
  grounded: number;
  with_citations: number;
  avg_keyword_overlap: number | null;
  avg_latency_ms: number | null;
}

export interface EvalRunItem {
  id: string;
  dataset_id: string;
  pipeline_id: string | null;
  status: string;
  summary: EvalSummary;
  results?: EvalResult[];
  created_at: string | null;
  finished_at: string | null;
}

export interface WorkspaceInfo {
  id: string;
  name: string;
  key_policy: string;
  settings: Record<string, unknown>;
}

export interface SessionMe {
  user: { id: string; email: string; name: string };
  workspace: { id: string; name: string } | null;
}

export interface SessionPayload {
  token: string;
  user: { id: string; email: string; name: string };
  workspace: { id: string; name: string };
}

export interface SignupData {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  company?: string;
  password: string;
}

export interface InvitePreview {
  email: string;
  role: string;
  status: string;
  workspace: string;
  needs_account: boolean;
}

export interface InviteItem {
  id: string;
  email: string;
  role: string;
  status: string;
  invited_by: string;
  created_at: string | null;
  expires_at: string | null;
  accept_url: string;
  email_error?: string;
}

export interface MemberItem {
  membership_id: string;
  role: string;
  user: { id: string; email: string; name: string };
}

export interface CredentialItem {
  id: string;
  provider: string;
  label: string;
  key_prefix: string;
  created_at: string | null;
}

export type ToolKind = "retriever" | "http" | "code" | "mcp";

export interface ToolItem {
  id: string;
  name: string;
  kind: ToolKind;
  description: string;
  input_schema: Record<string, unknown>;
  config: Record<string, unknown>;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface PromptVersion {
  version: number;
  content: string;
  notes: string;
  created_at: string | null;
}

export interface PromptItem {
  id: string;
  name: string;
  description: string;
  current_version: number;
  content?: string;
  versions?: PromptVersion[];
  created_at: string | null;
  updated_at: string | null;
}

export interface DSARItem {
  id: string;
  subject: string;
  kind: "export" | "erasure";
  status: string;
  result: Record<string, unknown>;
  created_at: string | null;
  finished_at: string | null;
}

export interface RetentionPolicy {
  retention_days: number | null;
  region: string;
  hipaa: boolean;
  allowed_providers: string[];
}

export const api = {
  // sources
  listSources: () => http<{ items: DataSource[] }>("/knowledge/sources"),
  createSource: (body: {
    name: string;
    type?: SourceType;
    modality?: Modality;
    connector?: string | null;
  }) => http<DataSource>("/knowledge/sources", { method: "POST", body: JSON.stringify(body) }),

  // documents
  listDocuments: (
    params: { q?: string; status?: string; source_id?: string; limit?: number; offset?: number } = {},
  ) => http<{ items: DocumentItem[]; total: number }>(`/knowledge/documents${qs(params)}`),
  getDocumentChunks: (id: string, params: { limit?: number; offset?: number } = {}) =>
    http<{ document: DocumentItem; items: ChunkItem[] }>(
      `/knowledge/documents/${id}/chunks${qs(params)}`,
    ),

  // multimodal — video ingestion (Azure video embedder)
  ingestVideo: (body: { url: string; name?: string; index_id?: string }) =>
    http<{ document_id: string; source_id: string; chunks: number; modality: string }>(
      "/ingest/video",
      { method: "POST", body: JSON.stringify(body) },
    ),

  // connectors / web crawl
  listConnectors: () => http<{ items: string[] }>("/knowledge/connectors"),
  crawl: (body: { url: string; max_pages?: number; same_domain?: boolean; name?: string }) =>
    http<{ source_id: string; documents: number; chunks: number; pages: string[] }>(
      "/knowledge/crawl",
      { method: "POST", body: JSON.stringify(body) },
    ),

  // indexes
  listIndexes: () => http<{ items: IndexItem[] }>("/knowledge/indexes"),
  createIndex: (body: {
    name: string;
    modality?: Modality;
    embedding_provider?: string;
    embedding_model?: string;
    chunk_size?: number;
    overlap?: number;
  }) => http<IndexItem>("/knowledge/indexes", { method: "POST", body: JSON.stringify(body) }),

  // pipelines
  listPipelines: () => http<{ items: PipelineItem[] }>("/pipelines"),
  createPipeline: (body: { name: string; graph?: PipelineGraphShape }) =>
    http<PipelineItem>("/pipelines", { method: "POST", body: JSON.stringify(body) }),
  getPipeline: (id: string) => http<PipelineItem>(`/pipelines/${id}`),
  updatePipeline: (id: string, body: { name?: string; graph?: PipelineGraphShape; status?: string }) =>
    http<PipelineItem>(`/pipelines/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  runPipeline: (id: string, body: { question: string; k?: number }) =>
    http<RunResult>(`/pipelines/${id}/run`, { method: "POST", body: JSON.stringify(body) }),

  // runs / traces
  listRuns: (params: { limit?: number; offset?: number } = {}) =>
    http<{ items: RunItem[]; total: number }>(`/runs${qs(params)}`),
  getRun: (id: string) => http<RunItem>(`/runs/${id}`),

  // deployments
  listDeployments: (params: { limit?: number; offset?: number } = {}) =>
    http<{ items: DeploymentItem[]; total: number }>(`/deployments${qs(params)}`),
  createDeployment: (body: { name: string; target_type: "pipeline" | "agent"; target_id: string }) =>
    http<DeploymentCreated>("/deployments", { method: "POST", body: JSON.stringify(body) }),
  getDeployment: (id: string) => http<DeploymentItem>(`/deployments/${id}`),
  pauseDeployment: (id: string) =>
    http<DeploymentItem>(`/deployments/${id}/pause`, { method: "POST" }),
  unpauseDeployment: (id: string) =>
    http<DeploymentItem>(`/deployments/${id}/unpause`, { method: "POST" }),

  // agents
  listAgents: () => http<{ items: AgentItem[] }>("/agents"),
  createAgent: (body: { name: string }) =>
    http<AgentItem>("/agents", { method: "POST", body: JSON.stringify(body) }),
  getAgent: (id: string) => http<AgentItem>(`/agents/${id}`),
  updateAgent: (id: string, body: Partial<Omit<AgentItem, "id" | "created_at" | "updated_at">>) =>
    http<AgentItem>(`/agents/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  runAgent: (id: string, body: { message: string; k?: number }) =>
    http<{ run_id: string; status: string; answer: string }>(`/agents/${id}/run`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // evals
  listDatasets: () => http<{ items: EvalDatasetItem[] }>("/evals"),
  createDataset: (body: { name: string; items: EvalQA[] }) =>
    http<EvalDatasetItem>("/evals", { method: "POST", body: JSON.stringify(body) }),
  getDataset: (id: string) => http<EvalDatasetItem>(`/evals/${id}`),
  listEvalRuns: (datasetId: string) =>
    http<{ items: EvalRunItem[] }>(`/evals/${datasetId}/runs`),
  runEval: (datasetId: string, body: { pipeline_id: string; k?: number }) =>
    http<EvalRunItem>(`/evals/${datasetId}/run`, { method: "POST", body: JSON.stringify(body) }),
  getEvalRun: (runId: string) => http<EvalRunItem>(`/eval-runs/${runId}`),

  // session / account
  getMe: () => http<SessionMe>("/auth/me"),
  login: (email: string, password: string) =>
    http<SessionPayload>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  signup: (data: SignupData) =>
    http<SessionPayload>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  forgotPassword: (email: string) =>
    http<{ ok: boolean; message: string }>("/auth/forgot", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, password: string) =>
    http<{ ok: boolean }>("/auth/reset", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    }),

  // invitations (accept flow — public)
  previewInvite: (token: string) => http<InvitePreview>(`/invites/${token}`),
  acceptInvite: (token: string, name: string, password: string) =>
    http<SessionPayload>(`/invites/${token}/accept`, {
      method: "POST",
      body: JSON.stringify({ name, password }),
    }),
  // invitations (management)
  listInvites: () => http<{ items: InviteItem[] }>("/workspace/invites"),
  createInvite: (email: string, role: string) =>
    http<InviteItem>("/workspace/invites", {
      method: "POST",
      body: JSON.stringify({ email, role }),
    }),
  revokeInvite: (id: string) =>
    http<void>(`/workspace/invites/${id}`, { method: "DELETE" }),
  resendInvite: (id: string) =>
    http<{ ok: boolean }>(`/workspace/invites/${id}/resend`, { method: "POST" }),

  // settings — workspace, members, provider credentials
  getWorkspace: () => http<WorkspaceInfo>("/workspace"),
  updateWorkspace: (body: { name?: string; key_policy?: string; settings?: Record<string, unknown> }) =>
    http<WorkspaceInfo>("/workspace", { method: "PUT", body: JSON.stringify(body) }),
  listMembers: () => http<{ items: MemberItem[] }>("/workspace/members"),
  addMember: (body: { email: string; role: string }) =>
    http<MemberItem>("/workspace/members", { method: "POST", body: JSON.stringify(body) }),
  removeMember: (id: string) =>
    http<void>(`/workspace/members/${id}`, { method: "DELETE" }),
  listCredentials: () => http<{ items: CredentialItem[] }>("/provider-credentials"),
  createCredential: (body: { provider: string; label: string; key: string }) =>
    http<CredentialItem>("/provider-credentials", { method: "POST", body: JSON.stringify(body) }),
  deleteCredential: (id: string) =>
    http<void>(`/provider-credentials/${id}`, { method: "DELETE" }),

  // tools
  listTools: () => http<{ items: ToolItem[] }>("/tools"),
  createTool: (body: {
    name: string;
    kind?: ToolKind;
    description?: string;
    input_schema?: Record<string, unknown>;
    config?: Record<string, unknown>;
    enabled?: boolean;
  }) => http<ToolItem>("/tools", { method: "POST", body: JSON.stringify(body) }),
  getTool: (id: string) => http<ToolItem>(`/tools/${id}`),
  updateTool: (id: string, body: Partial<Omit<ToolItem, "id" | "created_at" | "updated_at">>) =>
    http<ToolItem>(`/tools/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteTool: (id: string) => http<void>(`/tools/${id}`, { method: "DELETE" }),

  // prompts
  listPrompts: () => http<{ items: PromptItem[] }>("/prompts"),
  createPrompt: (body: { name: string; description?: string; content?: string }) =>
    http<PromptItem>("/prompts", { method: "POST", body: JSON.stringify(body) }),
  getPrompt: (id: string) => http<PromptItem>(`/prompts/${id}`),
  updatePrompt: (id: string, body: { name?: string; description?: string }) =>
    http<PromptItem>(`/prompts/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  addPromptVersion: (id: string, body: { content: string; notes?: string }) =>
    http<PromptVersion>(`/prompts/${id}/versions`, { method: "POST", body: JSON.stringify(body) }),
  deletePrompt: (id: string) => http<void>(`/prompts/${id}`, { method: "DELETE" }),

  // compliance — GDPR DSAR + retention
  listDSARs: () => http<{ items: DSARItem[] }>("/compliance/requests"),
  createDSAR: (body: { subject: string; kind: "export" | "erasure" }) =>
    http<DSARItem>("/compliance/requests", { method: "POST", body: JSON.stringify(body) }),
  processDSAR: (id: string) =>
    http<DSARItem>(`/compliance/requests/${id}/process`, { method: "POST" }),
  getRetention: () => http<RetentionPolicy>("/compliance/retention"),
  updateRetention: (body: { retention_days?: number; region?: string; hipaa?: boolean }) =>
    http<RetentionPolicy>("/compliance/retention", { method: "PUT", body: JSON.stringify(body) }),

  // notifications (header bell — dedicated inbox, separate from the audit log)
  listNotifications: (limit = 20) =>
    http<NotificationsResponse>(`/notifications${qs({ limit })}`),
  markNotificationRead: (id: string) =>
    http<NotificationItem>(`/notifications/${id}/read`, { method: "POST" }),
  markAllNotificationsRead: () =>
    http<{ marked_read: number }>("/notifications/read-all", { method: "POST" }),
  dismissNotification: (id: string) =>
    http<void>(`/notifications/${id}`, { method: "DELETE" }),
  clearNotifications: () => http<void>("/notifications", { method: "DELETE" }),

  // overview / dashboard
  getStats: () => http<OverviewStats>("/overview/stats"),
  getAnalytics: (days = 14) => http<Analytics>(`/analytics?days=${days}`),
  listAudit: (params: { limit?: number; offset?: number } = {}) =>
    http<{ items: AuditEvent[]; total: number }>(`/audit${qs(params)}`),

  // upload (multipart — no JSON content-type)
  uploadFile: async (
    file: File,
    opts: { sourceId?: string; indexId?: string } = {},
  ): Promise<IngestResult> => {
    const fd = new FormData();
    fd.append("file", file);
    if (opts.sourceId) fd.append("source_id", opts.sourceId);
    if (opts.indexId) fd.append("index_id", opts.indexId);
    const res = await fetch(`${BASE}/ingest`, { method: "POST", body: fd });
    if (!res.ok) {
      let msg = await res.text();
      try {
        const j = JSON.parse(msg);
        msg = j.detail?.error ?? j.detail ?? msg;
      } catch {
        /* keep raw */
      }
      throw new ApiError(res.status, msg);
    }
    return res.json() as Promise<IngestResult>;
  },

  // connections — bring-your-own integrations
  getConnectionCatalog: () => http<ConnectionCatalog>("/connections/catalog"),
  listConnections: (params: { capability?: string } = {}) =>
    http<{ items: ConnectionItem[] }>(`/connections${qs(params)}`),
  getConnection: (id: string) => http<ConnectionItem>(`/connections/${id}`),
  createConnection: (body: {
    name: string;
    capability: string;
    provider: string;
    values: Record<string, unknown>;
  }) => http<ConnectionItem>("/connections", { method: "POST", body: JSON.stringify(body) }),
  updateConnection: (id: string, body: { name?: string; values?: Record<string, unknown> }) =>
    http<ConnectionItem>(`/connections/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  testConnection: (id: string) =>
    http<{ ok: boolean; message: string; status: string }>(`/connections/${id}/test`, {
      method: "POST",
    }),
  deleteConnection: (id: string) =>
    http<void>(`/connections/${id}`, { method: "DELETE" }),
};

// --- Connection slots (G6) ---------------------------------------------------

export interface ConnectionItem {
  id: string;
  name: string;
  capability: string;
  provider: string;
  provider_label: string;
  config: Record<string, unknown>;
  secrets_set: string[];
  status: string;
  status_detail: string | null;
  last_tested_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

/** Optional per-capability Connection slots an agent can pin (null = workspace default). */
export interface AgentConnectionSlots {
  llm_connection_id: string | null;
  embedding_connection_id: string | null;
  vector_store_connection_id: string | null;
}

// --- Integration catalog (drives the dynamic "add connection" form) ----------
export interface CatalogField {
  name: string;
  label: string;
  type: "text" | "password" | "number" | "boolean" | "select";
  required: boolean;
  secret: boolean;
  placeholder: string;
  help: string;
  options: string[];
  default: string | number | boolean | null;
}

export interface CatalogProvider {
  capability: string;
  provider: string;
  label: string;
  description: string;
  docs_url: string;
  fields: CatalogField[];
}

export interface ConnectionCatalog {
  capabilities: Array<{ key: string; label: string; providers: CatalogProvider[] }>;
}
