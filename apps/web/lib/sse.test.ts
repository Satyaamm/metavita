import { describe, expect, it } from "vitest";
import { drainSseFrames } from "./sse";

describe("drainSseFrames", () => {
  it("parses complete frames and keeps the partial remainder", () => {
    const buffer = "event: citations\ndata: [1]\n\nevent: token\ndata: Hello\n\nevent: token\ndata: wor";
    const { events, rest } = drainSseFrames(buffer);
    expect(events).toEqual([
      { event: "citations", data: "[1]" },
      { event: "token", data: "Hello" },
    ]);
    expect(rest).toBe("event: token\ndata: wor");
  });

  it("joins multi-line data and defaults the event name", () => {
    const { events } = drainSseFrames("data: line1\ndata: line2\n\n");
    expect(events).toEqual([{ event: "message", data: "line1\nline2" }]);
  });

  it("ignores blank frames", () => {
    const { events, rest } = drainSseFrames("\n\nevent: done\ndata: \n\n");
    expect(events).toEqual([{ event: "done", data: "" }]);
    expect(rest).toBe("");
  });
});
