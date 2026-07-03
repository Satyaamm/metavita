"use client";

import { Button, Input, makeStyles } from "@fluentui/react-components";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { ApiError, api } from "@/lib/api";
import { useSessionStore } from "@/lib/stores/session";

const useStyles = makeStyles({
  form: { display: "flex", flexDirection: "column", gap: "16px" },
  field: { display: "flex", flexDirection: "column", gap: "6px" },
  labelRow: { display: "flex", justifyContent: "space-between", alignItems: "baseline" },
  lbl: {
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    color: "#5C6070",
  },
  submit: {
    backgroundColor: "#16181D",
    color: "#FFFFFF",
    border: "none",
    ":hover": { backgroundColor: "#000000", color: "#FFFFFF" },
    ":hover:active": { backgroundColor: "#000000", color: "#FFFFFF" },
  },
  error: { color: "#E5484D", fontSize: "13px" },
  link: { color: "#5B5BD6", textDecoration: "none", fontSize: "12px" },
  footerLink: { color: "#5B5BD6", textDecoration: "none", fontSize: "13px" },
});

export default function LoginPage() {
  const s = useStyles();
  const router = useRouter();
  const setSession = useSessionStore((st) => st.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const session = await api.login(email, password);
      setSession(session);
      router.replace("/");
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? "Invalid email or password."
          : "Unable to sign in. Please try again.",
      );
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Sign in"
      subtitle="Enter your credentials to access your workspace."
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link href="/signup" className={s.footerLink}>
            Sign up
          </Link>
        </>
      }
    >
      <form className={s.form} onSubmit={onSubmit}>
        <div className={s.field}>
          <span className={s.lbl}>Email</span>
          <Input
            type="email"
            value={email}
            onChange={(_, d) => setEmail(d.value)}
            placeholder="you@company.com"
            required
            autoComplete="email"
          />
        </div>
        <div className={s.field}>
          <div className={s.labelRow}>
            <span className={s.lbl}>Password</span>
            <Link href="/forgot" className={s.link}>
              Forgot password?
            </Link>
          </div>
          <Input
            type="password"
            value={password}
            onChange={(_, d) => setPassword(d.value)}
            required
            autoComplete="current-password"
          />
        </div>
        {error && <span className={s.error}>{error}</span>}
        <Button type="submit" appearance="primary" className={s.submit} disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}
