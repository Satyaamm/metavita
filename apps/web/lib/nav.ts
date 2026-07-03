/**
 * Navigation registry — single source of truth for the sidebar IA and routing.
 * The sidebar renders from this; active state is derived from the URL (usePathname),
 * never from React state, so every route is bookmarkable/shareable.
 */
import {
  Board20Filled,
  Board20Regular,
  Bot20Filled,
  Bot20Regular,
  Beaker20Filled,
  Beaker20Regular,
  ClipboardTask20Filled,
  ClipboardTask20Regular,
  Database20Filled,
  Database20Regular,
  DataPie20Filled,
  DataPie20Regular,
  DataTrending20Filled,
  DataTrending20Regular,
  DocumentMultiple20Filled,
  DocumentMultiple20Regular,
  Flowchart20Filled,
  Flowchart20Regular,
  type FluentIcon,
  Layer20Filled,
  Layer20Regular,
  Notepad20Filled,
  Notepad20Regular,
  PlugConnected20Filled,
  PlugConnected20Regular,
  Rocket20Filled,
  Rocket20Regular,
  Settings20Filled,
  Settings20Regular,
  ShieldTask20Filled,
  ShieldTask20Regular,
  Toolbox20Filled,
  Toolbox20Regular,
} from "@fluentui/react-icons";

export interface NavItem {
  key: string;
  label: string;
  href: string;
  Icon: FluentIcon;
  IconActive: FluentIcon;
}

export interface NavGroup {
  section: string;
  items: NavItem[];
}

export const NAV: NavGroup[] = [
  {
    section: "Overview",
    items: [
      { key: "dashboard", label: "Dashboard", href: "/", Icon: Board20Regular, IconActive: Board20Filled },
      { key: "connections", label: "Connections", href: "/connections", Icon: PlugConnected20Regular, IconActive: PlugConnected20Filled },
    ],
  },
  {
    section: "Knowledge",
    items: [
      { key: "sources", label: "Data Sources", href: "/knowledge/sources", Icon: Database20Regular, IconActive: Database20Filled },
      { key: "documents", label: "Documents", href: "/knowledge/documents", Icon: DocumentMultiple20Regular, IconActive: DocumentMultiple20Filled },
      { key: "indexes", label: "Indexes", href: "/knowledge/indexes", Icon: Layer20Regular, IconActive: Layer20Filled },
    ],
  },
  {
    section: "Build",
    items: [
      { key: "pipelines", label: "Pipelines", href: "/pipelines", Icon: Flowchart20Regular, IconActive: Flowchart20Filled },
      { key: "agents", label: "Agents", href: "/agents", Icon: Bot20Regular, IconActive: Bot20Filled },
      { key: "tools", label: "Tools", href: "/tools", Icon: Toolbox20Regular, IconActive: Toolbox20Filled },
      { key: "prompts", label: "Prompts", href: "/prompts", Icon: Notepad20Regular, IconActive: Notepad20Filled },
    ],
  },
  {
    section: "Test",
    items: [
      { key: "playground", label: "Playground", href: "/playground", Icon: Beaker20Regular, IconActive: Beaker20Filled },
      { key: "evals", label: "Evals", href: "/evals", Icon: ClipboardTask20Regular, IconActive: ClipboardTask20Filled },
    ],
  },
  {
    section: "Ship",
    items: [
      { key: "deployments", label: "Deployments", href: "/deployments", Icon: Rocket20Regular, IconActive: Rocket20Filled },
    ],
  },
  {
    section: "Observe",
    items: [
      { key: "traces", label: "Traces", href: "/traces", Icon: DataTrending20Regular, IconActive: DataTrending20Filled },
      { key: "analytics", label: "Analytics", href: "/analytics", Icon: DataPie20Regular, IconActive: DataPie20Filled },
      { key: "audit", label: "Audit log", href: "/audit", Icon: ShieldTask20Regular, IconActive: ShieldTask20Filled },
    ],
  },
  {
    section: "Settings",
    items: [
      { key: "settings", label: "Settings", href: "/settings", Icon: Settings20Regular, IconActive: Settings20Filled },
    ],
  },
];

/** A nav item is active when the path equals its href, or is nested under it. */
export function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}
