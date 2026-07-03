"use client";

import { Button, Field, Input, makeStyles } from "@fluentui/react-components";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { ApiError, api } from "@/lib/api";

const useStyles = makeStyles({
  form: { display: "flex", flexDirection: "column", gap: "14px" },
  submit: {
    backgroundColor: "#16181D",
    color: "#FFFFFF",
    border: "none",
    ":hover": { backgroundColor: "#000000", color: "#FFFFFF" },
    ":hover:active": { backgroundColor: "#000000", color: "#FFFFFF" },
  },
  error: { color: "#E5484D", fontSize: "13px" },
  note: { color: "#5C6070", fontSize: "13px" },
  link: { color: "#5B5BD6", textDecoration: "none", fontSize: "13px" },
});

export default function ResetPage() {
  const s = useStyles();
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(
        err instanceof ApiError && (err.status === 400 || err.status === 410)
          ? "This reset link is invalid or has expired."
          : "Unable to reset your password. Please try again.",
      );
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Set a new password"
      footer={
        <Link href="/login" className={s.link}>
          Back to sign in
        </Link>
      }
    >
      {done ? (
        <p className={s.note}>
          Your password has been updated. You can now{" "}
          <Link href="/login" className={s.link}>
            sign in
          </Link>
          .
        </p>
      ) : (
        <form className={s.form} onSubmit={onSubmit}>
          <Field label="New password" hint="At least 8 characters.">
            <Input
              type="password"
              value={password}
              onChange={(_, d) => setPassword(d.value)}
              required
              autoComplete="new-password"
            />
          </Field>
          {error && <span className={s.error}>{error}</span>}
          <Button type="submit" appearance="primary" className={s.submit} disabled={busy}>
            {busy ? "Updating…" : "Update password"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
