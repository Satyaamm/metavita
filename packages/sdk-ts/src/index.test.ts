import { describe, expect, it, vi } from "vitest";
import { MetaVita, MetaVitaError } from "./index";

function mockFetch(handler: (url: string, init: RequestInit) => { status?: number; body?: unknown }) {
  return vi.fn(async (url: string, init: RequestInit) => {
    const { status = 200, body = {} } = handler(url, init);
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
      text: async () => (typeof body === "string" ? body : JSON.stringify(body)),
    } as Response;
  });
}

describe("MetaVita SDK", () => {
  it("requires a baseUrl", () => {
    expect(() => new MetaVita({ baseUrl: "" })).toThrow();
  });

  it("serve() posts to /serve with the deployment key", async () => {
    const fetch = mockFetch((url, init) => {
      expect(url).toBe("https://api.test/serve/dep-1");
      expect((init.headers as Record<string, string>).Authorization).toBe("Bearer mv_key");
      return { body: { answer: "hi", citations: [] } };
    });
    const mv = new MetaVita({ baseUrl: "https://api.test/", apiKey: "mv_key", fetch });
    const res = await mv.serve("dep-1", { question: "hello" });
    expect(res.answer).toBe("hi");
    expect(fetch).toHaveBeenCalledOnce();
  });

  it("query() uses the workspace token, not the api key", async () => {
    const fetch = mockFetch((_url, init) => {
      expect((init.headers as Record<string, string>).Authorization).toBe("Bearer jwt");
      return { body: { answer: "a", citations: [] } };
    });
    const mv = new MetaVita({ baseUrl: "https://api.test", token: "jwt", fetch });
    await mv.query({ question: "q" });
  });

  it("throws MetaVitaError on non-2xx", async () => {
    const fetch = mockFetch(() => ({ status: 401, body: "nope" }));
    const mv = new MetaVita({ baseUrl: "https://api.test", apiKey: "k", fetch });
    await expect(mv.serve("d", { question: "x" })).rejects.toBeInstanceOf(MetaVitaError);
  });
});
