import { describe, expect, it } from "vitest";
import { curlSnippet, serveUrl, widgetSnippet } from "./widget";

const BASE = "https://app.metavita.dev";
const ID = "dep_123";

describe("widget snippets", () => {
  it("serveUrl builds the endpoint", () => {
    expect(serveUrl(ID, BASE)).toBe("https://app.metavita.dev/serve/dep_123");
  });

  it("curlSnippet includes endpoint, key, and a sample question", () => {
    const s = curlSnippet(ID, "mv_secret", BASE);
    expect(s).toContain("/serve/dep_123");
    expect(s).toContain("Authorization: Bearer mv_secret");
    expect(s).toContain('"question"');
  });

  it("widgetSnippet embeds the deployment id", () => {
    expect(widgetSnippet(ID, BASE)).toContain('data-deployment="dep_123"');
    expect(widgetSnippet(ID, BASE)).toContain("widget.js");
  });
});
