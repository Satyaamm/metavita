"use client";

import {
  Avatar,
  Button,
  Caption1,
  CounterBadge,
  Divider,
  Menu,
  MenuDivider,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
  Popover,
  PopoverSurface,
  PopoverTrigger,
  Text,
  Tooltip,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import {
  Alert20Regular,
  CheckmarkCircle20Filled,
  Dismiss16Regular,
  ErrorCircle20Filled,
  Info20Filled,
  Person20Regular,
  Settings20Regular,
  SignOut20Regular,
  Warning20Filled,
} from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { NotificationSeverity } from "@/lib/api";
import { useNotificationsStore } from "@/lib/stores/notifications";
import { useSessionStore, signOut } from "@/lib/stores/session";
import { useWorkspaceStore } from "@/lib/stores/settings";
import { appTokens, palette } from "../app/theme";
import { HeaderSearch } from "./HeaderSearch";

const useStyles = makeStyles({
  header: {
    height: appTokens.headerHeight,
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "0 24px",
    backgroundColor: appTokens.surfaceBg,
    borderBottom: `1px solid ${appTokens.border}`,
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  spacer: { flex: 1 },
  search: { width: "340px", maxWidth: "40vw" },
  bellWrap: { position: "relative", display: "inline-flex" },
  badge: { position: "absolute", top: "2px", right: "2px", pointerEvents: "none" },
  panel: { width: "360px", padding: 0, maxHeight: "70vh", display: "flex", flexDirection: "column" },
  panelHead: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 16px",
    borderBottom: `1px solid ${appTokens.border}`,
  },
  list: { overflowY: "auto", display: "flex", flexDirection: "column" },
  row: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "12px 16px",
    width: "100%",
    textAlign: "left",
    border: "none",
    borderBottom: `1px solid ${appTokens.border}`,
    background: "transparent",
    cursor: "pointer",
    textDecoration: "none",
    color: palette.ink,
    ":hover": { backgroundColor: tokens.colorNeutralBackground3 },
  },
  rowBody: { display: "flex", flexDirection: "column", gap: "2px", minWidth: 0, flex: 1 },
  rowDetail: {
    color: palette.inkSubtle,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  empty: { padding: "32px 16px", textAlign: "center", color: palette.inkSubtle },
  unreadDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: palette.brandPrimary,
    flexShrink: 0,
    alignSelf: "center",
  },
  profileBtn: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    border: "none",
    background: "transparent",
    cursor: "pointer",
    padding: "4px 6px",
    borderRadius: appTokens.radiusControl,
    ":hover": { backgroundColor: tokens.colorNeutralBackground3 },
  },
  profileMeta: { display: "flex", flexDirection: "column", lineHeight: 1.2, textAlign: "left" },
  menuHead: { padding: "8px 12px", display: "flex", flexDirection: "column", gap: "2px" },
});

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function SeverityIcon({ severity }: { severity: NotificationSeverity }) {
  switch (severity) {
    case "success":
      return <CheckmarkCircle20Filled style={{ color: "#1F9D55" }} />;
    case "warning":
      return <Warning20Filled style={{ color: "#C77700" }} />;
    case "error":
      return <ErrorCircle20Filled style={{ color: "#C4314B" }} />;
    default:
      return <Info20Filled style={{ color: palette.brandPrimary }} />;
  }
}

export function Header() {
  const styles = useStyles();
  const { items, unread, fetch, markRead, markAllRead, dismiss, clearAll } =
    useNotificationsStore();
  const workspace = useWorkspaceStore((s) => s.workspace);
  const fetchWorkspace = useWorkspaceStore((s) => s.fetch);
  const me = useSessionStore((s) => s.me);
  const fetchSession = useSessionStore((s) => s.fetch);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    fetchWorkspace();
    fetchSession();
    fetch();
    const id = setInterval(fetch, 30_000); // poll the inbox
    return () => clearInterval(id);
  }, [fetch, fetchWorkspace, fetchSession]);

  // Real account when signed in; graceful fallback in dev (no auth token yet).
  const displayName = me?.user.name ?? workspace?.name ?? "MetaVita";
  const displayEmail = me?.user.email ?? "Not signed in";

  return (
    <header className={styles.header}>
      <HeaderSearch />

      <div className={styles.spacer} />

      <Popover open={open} onOpenChange={(_, d) => setOpen(d.open)} positioning="below-end">
        <span className={styles.bellWrap}>
          <Tooltip content="Notifications" relationship="label">
            <PopoverTrigger disableButtonEnhancement>
              <Button appearance="subtle" icon={<Alert20Regular />} aria-label="Notifications" />
            </PopoverTrigger>
          </Tooltip>
          {unread > 0 && (
            <CounterBadge
              className={styles.badge}
              count={unread}
              size="small"
              color="danger"
              overflowCount={9}
            />
          )}
        </span>
        <PopoverSurface className={styles.panel}>
          <div className={styles.panelHead}>
            <Text weight="semibold">Notifications</Text>
            <div style={{ display: "flex", gap: 4 }}>
              <Button appearance="subtle" size="small" onClick={markAllRead} disabled={unread === 0}>
                Mark all read
              </Button>
              <Button
                appearance="subtle"
                size="small"
                onClick={clearAll}
                disabled={items.length === 0}
              >
                Clear
              </Button>
            </div>
          </div>
          {items.length === 0 ? (
            <div className={styles.empty}>
              <Text>You&apos;re all caught up.</Text>
            </div>
          ) : (
            <div className={styles.list}>
              {items.map((n) => {
                const inner = (
                  <>
                    <SeverityIcon severity={n.severity} />
                    <div className={styles.rowBody}>
                      <Text size={300} weight={n.read ? "regular" : "semibold"}>
                        {n.title}
                      </Text>
                      {n.detail && <Caption1 className={styles.rowDetail}>{n.detail}</Caption1>}
                      <Caption1 style={{ color: palette.inkSubtle }}>{timeAgo(n.created_at)}</Caption1>
                    </div>
                    {!n.read && <span className={styles.unreadDot} />}
                    <Button
                      appearance="subtle"
                      size="small"
                      icon={<Dismiss16Regular />}
                      aria-label="Dismiss"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        dismiss(n.id);
                      }}
                    />
                  </>
                );
                return n.link ? (
                  <Link
                    key={n.id}
                    href={n.link}
                    className={styles.row}
                    onClick={() => {
                      markRead(n.id);
                      setOpen(false);
                    }}
                  >
                    {inner}
                  </Link>
                ) : (
                  <button
                    key={n.id}
                    type="button"
                    className={styles.row}
                    onClick={() => markRead(n.id)}
                  >
                    {inner}
                  </button>
                );
              })}
            </div>
          )}
        </PopoverSurface>
      </Popover>

      <Menu>
        <MenuTrigger disableButtonEnhancement>
          <button type="button" className={styles.profileBtn} aria-label="Account menu">
            <Avatar name={displayName} color="colorful" size={32} aria-hidden />
            <span className={styles.profileMeta}>
              <Text size={200} weight="semibold">
                {displayName}
              </Text>
              <Text size={100} style={{ color: palette.inkSubtle }}>
                {workspace?.name ?? "Workspace"}
              </Text>
            </span>
          </button>
        </MenuTrigger>
        <MenuPopover>
          <div className={styles.menuHead}>
            <Text weight="semibold" size={300}>
              {displayName}
            </Text>
            <Text size={200} style={{ color: palette.inkSubtle }}>
              {displayEmail}
            </Text>
            {workspace?.name && (
              <Caption1 style={{ color: palette.inkSubtle }}>Workspace · {workspace.name}</Caption1>
            )}
          </div>
          <Divider />
          <MenuList>
            <Link href="/profile" style={{ textDecoration: "none", color: "inherit" }}>
              <MenuItem icon={<Person20Regular />}>Profile</MenuItem>
            </Link>
            <Link href="/settings" style={{ textDecoration: "none", color: "inherit" }}>
              <MenuItem icon={<Settings20Regular />}>Account settings</MenuItem>
            </Link>
            <MenuDivider />
            <MenuItem icon={<SignOut20Regular />} onClick={signOut}>
              Sign out
            </MenuItem>
          </MenuList>
        </MenuPopover>
      </Menu>
    </header>
  );
}
