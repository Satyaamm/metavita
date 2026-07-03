/**
 * MetaVita brand mark — an original logo: a central retrieval "hub" linked to
 * three nodes (a knowledge graph), on the violet→indigo brand gradient. Reads as
 * connected intelligence (RAG/agents) that grows (vita). Self-contained SVG so it
 * works in the sidebar, headers, and as a favicon.
 */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label="MetaVita"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="metavitaLogoGradient" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6E6AF0" />
          <stop offset="1" stopColor="#9A5BE6" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#metavitaLogoGradient)" />
      <g stroke="#FFFFFF" strokeWidth="1.6" strokeLinecap="round" opacity="0.9">
        <line x1="16" y1="16" x2="16" y2="8.5" />
        <line x1="16" y1="16" x2="9.5" y2="21" />
        <line x1="16" y1="16" x2="22.5" y2="21" />
      </g>
      <g fill="#FFFFFF">
        <circle cx="16" cy="16" r="3" />
        <circle cx="16" cy="8.5" r="2.1" />
        <circle cx="9.5" cy="21" r="2.1" />
        <circle cx="22.5" cy="21" r="2.1" />
      </g>
    </svg>
  );
}
