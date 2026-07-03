/** Pure SSE frame parsing — used by streaming chat (playground, dashboard). */

export interface SseEvent {
  event: string;
  data: string;
}

/**
 * Drain complete `event:`/`data:` frames from an accumulated buffer.
 * Returns parsed events plus the unparsed remainder (a partial trailing frame).
 */
export function drainSseFrames(buffer: string): { events: SseEvent[]; rest: string } {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  const events: SseEvent[] = [];
  for (const frame of parts) {
    if (!frame.trim()) continue;
    const event = frame.match(/^event: (.*)$/m)?.[1] ?? "message";
    const data = frame
      .split("\n")
      .filter((l) => l.startsWith("data: "))
      .map((l) => l.slice(6))
      .join("\n");
    events.push({ event, data });
  }
  return { events, rest };
}
