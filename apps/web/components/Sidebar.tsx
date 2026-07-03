"use client";

import { Caption1, Text, makeStyles, mergeClasses, tokens } from "@fluentui/react-components";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { appTokens, palette, tints } from "../app/theme";
import { NAV, isActive } from "../lib/nav";
import { Logo } from "./Logo";

const useStyles = makeStyles({
  aside: {
    width: appTokens.sidebarWidth,
    flexShrink: 0,
    backgroundColor: appTokens.surfaceBg,
    borderRight: `1px solid ${appTokens.border}`,
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    position: "sticky",
    top: 0,
  },
  brandRow: {
    height: appTokens.headerHeight,
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "0 20px",
    borderBottom: `1px solid ${appTokens.border}`,
    flexShrink: 0,
  },
  brandMark: {
    width: "28px",
    height: "28px",
    borderRadius: "8px",
    background: `linear-gradient(135deg, ${palette.brandPrimary}, #8B5BE6)`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontWeight: 700,
    fontSize: "15px",
  },
  brandName: { fontWeight: 700, letterSpacing: "-0.01em" },
  nav: { padding: "14px 12px", display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto", flex: 1 },
  sectionLabel: {
    padding: "0 12px 4px",
    color: tokens.colorNeutralForeground4,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    fontSize: "11px",
  },
  group: { display: "flex", flexDirection: "column", gap: "2px" },
  item: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    height: "36px",
    padding: "0 12px",
    borderRadius: appTokens.radiusControl,
    color: palette.inkSubtle,
    textDecoration: "none",
    fontSize: "14px",
    fontWeight: 500,
    ":hover": { backgroundColor: tokens.colorNeutralBackground3, color: palette.ink },
  },
  itemActive: {
    backgroundColor: palette.brandSoft,
    color: palette.brandPrimary,
    fontWeight: 600,
    ":hover": { backgroundColor: palette.brandSoft, color: palette.brandPrimary },
  },
  footer: { padding: "14px", borderTop: `1px solid ${appTokens.border}`, flexShrink: 0 },
  upsell: {
    borderRadius: appTokens.radiusCard,
    padding: "14px",
    background: `linear-gradient(135deg, ${palette.brandSoft}, ${tints.lilac})`,
    border: `1px solid ${appTokens.border}`,
  },
});

export function Sidebar() {
  const styles = useStyles();
  const pathname = usePathname();

  return (
    <aside className={styles.aside}>
      <div className={styles.brandRow}>
        <Logo size={28} />
        <Text className={styles.brandName} size={400}>
          MetaVita
        </Text>
      </div>

      <nav className={styles.nav}>
        {NAV.map((group) => (
          <div key={group.section} className={styles.group}>
            <Caption1 className={styles.sectionLabel}>{group.section}</Caption1>
            {group.items.map(({ key, label, href, Icon, IconActive }) => {
              const active = isActive(pathname, href);
              const Glyph = active ? IconActive : Icon;
              return (
                <Link
                  key={key}
                  href={href}
                  className={mergeClasses(styles.item, active && styles.itemActive)}
                >
                  <Glyph />
                  {label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className={styles.footer}>
        <div className={styles.upsell}>
          <Text weight="semibold" size={200} block>
            Open-core
          </Text>
          <Caption1>Self-host MetaVita or run it as managed SaaS.</Caption1>
        </div>
      </div>
    </aside>
  );
}
