"use client";

import { Button, Field, Input, makeStyles } from "@fluentui/react-components";
import Link from "next/link";
import { useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { api } from "@/lib/api";

const useStyles = makeStyles({
  form: { display: "flex", flexDirection: "column", gap: "14px" },
  submit: {
    backgroundColor: "#16181D",
    color: "#FFFFFF",
    border: "none",
    ":hover": { backgroundColor: "#000000", color: "#FFFFFF" },
    ":hover:active": { backgroundColor: "#000000", color: "#FFFFFF" },
  },
  note: { color: "#5C6070", fontSize: "13px", lineHeight: 1.5 },
  link: { color: "#5B5BD6", textDecoration: "none", fontSize: "13px" },
});

export default function ForgotPage() {
  const s = useStyles();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await api.forgotPassword(email);
      setSent(res.message);
    } catch {
      // The endpoint is deliberately generic; treat any response as handled.
      setSent("If an account exists and an email provider is connected, a reset link was sent.");
    }
    setBusy(false);
  }

  return (
    <AuthShell
      title="Reset your password"
      subtitle="Enter your email and we'll send a reset link through your workspace's email provider."
      footer={
        <Link href="/login" className={s.link}>
          Back to sign in
        </Link>
      }
    >
      {sent ? (
        <p className={s.note}>{sent}</p>
      ) : (
        <form className={s.form} onSubmit={onSubmit}>
          <Field label="Email">
            <Input
              type="email"
              value={email}
              onChange={(_, d) => setEmail(d.value)}
              placeholder="you@company.com"
              required
              autoComplete="email"
            />
          </Field>
          <Button type="submit" appearance="primary" className={s.submit} disabled={busy}>
            {busy ? "Sending…" : "Send reset link"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
