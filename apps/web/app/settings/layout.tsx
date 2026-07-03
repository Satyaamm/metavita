"use client";

import { Tab, TabList, Title3, makeStyles } from "@fluentui/react-components";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const TABS = [
  { value: "/settings", label: "Workspace" },
  { value: "/settings/members", label: "Members" },
  { value: "/settings/security", label: "Security" },
  { value: "/settings/compliance", label: "Compliance" },
];

const useStyles = makeStyles({
  head: { display: "flex", flexDirection: "column", gap: "8px" },
});

export default function SettingsLayout({ children }: { children: ReactNode }) {
  const styles = useStyles();
  const pathname = usePathname();
  const selected = TABS.some((t) => t.value === pathname) ? pathname : "/settings";

  return (
    <>
      <div className={styles.head}>
        <Title3>Settings</Title3>
        <TabList selectedValue={selected}>
          {TABS.map((t) => (
            <Tab key={t.value} value={t.value}>
              <Link href={t.value} style={{ textDecoration: "none", color: "inherit" }}>
                {t.label}
              </Link>
            </Tab>
          ))}
        </TabList>
      </div>
      {children}
    </>
  );
}
