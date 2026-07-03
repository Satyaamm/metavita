"use client";

import { makeStyles } from "@fluentui/react-components";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import { appTokens } from "../app/theme";
import { getToken } from "../lib/api";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

const useStyles = makeStyles({
  root: { display: "flex", minHeight: "100vh", backgroundColor: appTokens.canvasBg },
  main: { flex: 1, display: "flex", flexDirection: "column", minWidth: 0 },
  content: {
    flex: 1,
    overflowY: "auto",
    padding: "28px 32px",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
});

// Routes rendered without the app chrome (no sidebar/header) and without a session.
const PUBLIC_PREFIXES = ["/login", "/signup", "/forgot", "/reset", "/invite"];

function isPublic(pathname: string): boolean {
  return PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function AppShell({ children }: { children: ReactNode }) {
  const styles = useStyles();
  const pathname = usePathname();
  const router = useRouter();
  const publicRoute = isPublic(pathname);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (publicRoute) {
      setChecked(true);
      return;
    }
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setChecked(true);
  }, [publicRoute, pathname, router]);

  // Auth pages: render bare.
  if (publicRoute) return <>{children}</>;

  // Protected pages: hold render until the guard passes so the shell never flashes
  // to a signed-out visitor.
  if (!checked) return null;

  return (
    <div className={styles.root}>
      <Sidebar />
      <div className={styles.main}>
        <Header />
        <main className={styles.content}>{children}</main>
      </div>
    </div>
  );
}
