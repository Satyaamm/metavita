"use client";

import { Button, Input, makeStyles } from "@fluentui/react-components";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { ApiError, api } from "@/lib/api";
import { useSessionStore } from "@/lib/stores/session";

const useStyles = makeStyles({
  form: { display: "flex", flexDirection: "column", gap: "14px" },
  twoCol: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" },
  field: { display: "flex", flexDirection: "column", gap: "6px" },
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
  link: { color: "#5B5BD6", textDecoration: "none", fontSize: "13px" },
});

export default function SignupPage() {
  const s = useStyles();
  const router = useRouter();
  const setSession = useSessionStore((st) => st.setSession);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    company: "",
    password: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: keyof typeof form) => (_: unknown, d: { value: string }) =>
    setForm((f) => ({ ...f, [k]: d.value }));

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const session = await api.signup({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        phone: form.phone || undefined,
        company: form.company || undefined,
        password: form.password,
      });
      setSession(session);
      router.replace("/");
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? "That email is already registered."
          : "Unable to create your account. Please try again.",
      );
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Tell us a bit about you to set up your workspace."
      wide
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className={s.link}>
            Sign in
          </Link>
        </>
      }
    >
      <form className={s.form} onSubmit={onSubmit}>
        <div className={s.twoCol}>
          <div className={s.field}>
            <span className={s.lbl}>First name</span>
            <Input value={form.first_name} onChange={set("first_name")} required autoComplete="given-name" />
          </div>
          <div className={s.field}>
            <span className={s.lbl}>Last name</span>
            <Input value={form.last_name} onChange={set("last_name")} required autoComplete="family-name" />
          </div>
        </div>
        <div className={s.field}>
          <span className={s.lbl}>Work email</span>
          <Input
            type="email"
            value={form.email}
            onChange={set("email")}
            placeholder="you@company.com"
            required
            autoComplete="email"
          />
        </div>
        <div className={s.twoCol}>
          <div className={s.field}>
            <span className={s.lbl}>Phone number</span>
            <Input
              type="tel"
              value={form.phone}
              onChange={set("phone")}
              placeholder="+1 555 000 1234"
              autoComplete="tel"
            />
          </div>
          <div className={s.field}>
            <span className={s.lbl}>Company</span>
            <Input value={form.company} onChange={set("company")} autoComplete="organization" />
          </div>
        </div>
        <div className={s.field}>
          <span className={s.lbl}>Password</span>
          <Input
            type="password"
            value={form.password}
            onChange={set("password")}
            placeholder="At least 8 characters"
            required
            autoComplete="new-password"
          />
        </div>
        {error && <span className={s.error}>{error}</span>}
        <Button type="submit" appearance="primary" className={s.submit} disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}
