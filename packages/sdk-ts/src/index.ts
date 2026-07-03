/**
 * Official TypeScript SDK for the MetaVita agentic RAG platform.
 *
 * A thin, typed wrapper over the REST API. Works in the browser, Node 18+, and
 * edge runtimes (uses the global `fetch`). Two auth modes:
 *   - `apiKey`  → a deployment key for the public `/serve/{id}` surface.
 *   - `token`   → a workspace JWT for authenticated builder endpoints.
 *
 * @example
 *   const mv = new MetaVita({ baseUrl: "https://api.metavita.dev", apiKey: "mv_..." });
 *   const res = await mv.serve(deploymentId, { question: "What changed in v2?" });
 *   console.log(res.answer, res.citations);
 */

export interface MetaVitaOptions {
  /** API base, e.g. "https://api.metavita.dev". No trailing slash needed. */
  baseUrl: string;
  /** Deployment API key (Bearer) for `/serve`. */
  apiKey?: string;
  /** Workspace JWT for authenticated endpoints. */
  token?: string;
  /** Optional workspace id header (dev/multi-workspace). */
  workspaceId?: string;
  /** Custom fetch (defaults to global fetch). */
  fetch?: typeof fetch;
}

export interface Citation {
  marker: number;
  document_id: string | null;
  chunk_index: number | null;
  snippet: string;
}

export interface AnswerResponse {
  answer: string;
  citations: Citation[];
  run_id?: string;
}

export interface RunResult extends AnswerResponse {
  run_id: string;
  status: string;
}

export class MetaVitaError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "MetaVitaError";
  }
}

export class MetaVita {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly token?: string;
  private readonly workspaceId?: string;
  private readonly _fetch: typeof fetch;

  constructor(opts: MetaVitaOptions) {
    if (!opts.baseUrl) throw new Error("MetaVita: baseUrl is required");
    this.baseUrl = opts.baseUrl.replace(/\/$/, "");
    this.apiKey = opts.apiKey;
    this.token = opts.token;
    this.workspaceId = opts.workspaceId;
    this._fetch = opts.fetch ?? globalThis.fetch;
    if (!this._fetch) throw new Error("MetaVita: no fetch available; pass opts.fetch");
  }

  private async request<T>(path: string, init: RequestInit & { auth?: "key" | "token" } = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((init.headers as Record<string, string>) ?? {}),
    };
    if (init.auth === "key" && this.apiKey) headers.Authorization = `Bearer ${this.apiKey}`;
    if (init.auth !== "key" && this.token) headers.Authorization = `Bearer ${this.token}`;
    if (this.workspaceId) headers["X-Workspace-Id"] = this.workspaceId;

    const res = await this._fetch(`${this.baseUrl}${path}`, { ...init, headers });
    if (!res.ok) throw new MetaVitaError(res.status, await res.text());
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  }

  /** Run a published deployment by its API key (public serving surface). */
  serve(deploymentId: string, body: { question: string; k?: number }): Promise<AnswerResponse> {
    return this.request(`/serve/${deploymentId}`, {
      method: "POST",
      body: JSON.stringify(body),
      auth: "key",
    });
  }

  /** Ask the workspace's default knowledge base. */
  query(body: { question: string; k?: number }): Promise<AnswerResponse> {
    return this.request(`/query`, { method: "POST", body: JSON.stringify(body) });
  }

  /** Run a pipeline by id. */
  runPipeline(pipelineId: string, body: { question: string; k?: number }): Promise<RunResult> {
    return this.request(`/pipelines/${pipelineId}/run`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  /** Run an agent by id (ReAct tool loop). */
  runAgent(
    agentId: string,
    body: { message: string; k?: number },
  ): Promise<{ run_id: string; status: string; answer: string }> {
    return this.request(`/agents/${agentId}/run`, { method: "POST", body: JSON.stringify(body) });
  }

  /** List pipelines in the workspace. */
  listPipelines(): Promise<{ items: Array<{ id: string; name: string; status: string }> }> {
    return this.request(`/pipelines`);
  }

  /** List agents in the workspace. */
  listAgents(): Promise<{ items: Array<{ id: string; name: string; model: string }> }> {
    return this.request(`/agents`);
  }

  /** Crawl a web page into the knowledge base. */
  crawl(body: {
    url: string;
    max_pages?: number;
    same_domain?: boolean;
    name?: string;
  }): Promise<{ source_id: string; documents: number; chunks: number; pages: string[] }> {
    return this.request(`/knowledge/crawl`, { method: "POST", body: JSON.stringify(body) });
  }
}

export default MetaVita;
