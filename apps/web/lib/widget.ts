/** Pure snippet generators for a deployment's serving endpoint (curl + embed widget). */

export function serveUrl(deploymentId: string, base: string): string {
  return `${base}/serve/${deploymentId}`;
}

export function curlSnippet(deploymentId: string, apiKey: string, base: string): string {
  return [
    `curl -X POST ${serveUrl(deploymentId, base)} \\`,
    `  -H "Authorization: Bearer ${apiKey}" \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '{"question": "What are the key findings?"}'`,
  ].join("\n");
}

export function widgetSnippet(
  deploymentId: string,
  base: string,
  apiKey = "mv_YOUR_API_KEY",
): string {
  return [
    `<script src="${base}/widget.js"`,
    `        data-deployment="${deploymentId}"`,
    `        data-api-key="${apiKey}"`,
    `        data-title="Ask us anything"`,
    `        defer></script>`,
  ].join("\n");
}
