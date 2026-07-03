/**
 * Centralized design tokens for MetaVita — the single source of truth for color.
 *
 * Brand: indigo/violet on a soft cool canvas (the preferred look). The pastel
 * `tints` set (extracted from the SaaS reference) is kept available for category
 * cards, status chips, and accents — so the full palette lives in one place.
 *
 * Built on Fluent UI v9: the `brand` ramp drives `createLightTheme`/`createDarkTheme`;
 * `palette`, `tints`, and `appTokens` cover app chrome the Fluent theme doesn't.
 * Edit this one file to re-skin the whole app.
 */
import {
  type BrandVariants,
  type Theme,
  createDarkTheme,
  createLightTheme,
} from "@fluentui/react-components";

/** Indigo/violet brand ramp. `brand[80]` (#5B5BD6) is the primary fill (light). */
export const brand: BrandVariants = {
  10: "#07061A",
  20: "#11103A",
  30: "#1B1A55",
  40: "#242370",
  50: "#2E2D8B",
  60: "#4040AE",
  70: "#4E4EC6",
  80: "#5B5BD6",
  90: "#7474DE",
  100: "#8B8BE6",
  110: "#A0A0EC",
  120: "#B6B6F2",
  130: "#CCCCF6",
  140: "#DEDEFA",
  150: "#EDEDFC",
  160: "#F6F6FE",
};

/** Raw semantic colors used by app chrome (kept outside the Fluent neutral ramp). */
export const palette = {
  brandPrimary: "#5B5BD6",
  brandHover: "#5151C9",
  brandSoft: "#EDEDFC", // violet-tinted surface (active nav, chips)
  canvas: "#F6F7F9", // soft cool app body
  surface: "#FFFFFF", // cards / sidebar / header
  ink: "#16181D", // headings / primary text
  inkSubtle: "#5C6070", // secondary text
  border: "#E6E8EC", // hairline border
  danger: "#E5484D",
} as const;

/** Pastel category tints (feature cards, status chips, accents) — the full palette. */
export const tints = {
  lilac: "#E9E3F6",
  sky: "#DCE2F6",
  peach: "#FBE7D2",
  sage: "#E6EDD9",
  rose: "#F2DCEC",
  slate: "#E6E9EB",
} as const;

export const metavitaLightTheme: Theme = {
  ...createLightTheme(brand),
};

export const metavitaDarkTheme: Theme = {
  ...createDarkTheme(brand),
};

/** App-shell layout + chrome tokens (not part of the Fluent theme). */
export const appTokens = {
  sidebarWidth: "260px",
  sidebarCollapsedWidth: "72px",
  headerHeight: "60px",
  canvasBg: palette.canvas,
  surfaceBg: palette.surface,
  border: palette.border,
  radiusCard: "12px",
  radiusControl: "8px",
  shadowCard: "0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06)",
} as const;
