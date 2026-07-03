"use client";

import { Badge, Button, Field, Input, Spinner, makeStyles } from "@fluentui/react-components";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { type InvitePreview, api } from "@/lib/api";
import { useSessionStore } from "@/lib/stores/session";

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
  note: { color: "#5C6070", fontSize: "13px", lineHeight: 1.5 },
  meta: { display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "#5C6070" },
  link: { color: "#5B5BD6", textDecoration: "none", fontSize: "13px" },
});

export default function InviteAcceptPage() {
  const s = useStyles();
  const router = useRouter();
  const params = useParams<{ token: string }>();
  const token = params.token;
  const setSession = useSessionStore((st) => st.setSession);

  const [preview, setPreview] = useState<InvitePreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .previewInvite(token)
      .then(setPreview)
      .catch(() => setError("This invitation link is invalid."))
      .finally(() => setLoading(false));
  }, [token]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (preview?.needs_account && password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const session = await api.acceptInvite(token, name, password);
      setSession(session);
      router.replace("/");
    } catch {
      setError("Unable to accept this invitation. It may have expired.");
      setBusy(false);
    }
  }

  const invalid =
    preview && preview.status !== "pending"
      ? `This invitation has been ${preview.status}.`
      : null;

  return (
    <AuthShell
      title="Accept invitation"
      subtitle={preview ? `Join ${preview.workspace} on MetaVita.` : undefined}
      footer={
        <Link href="/login" className={s.link}>
          Back to sign in
        </Link>
      }
    >
      {loading ? (
        <Spinner label="Loading invitation…" />
      ) : error && !preview ? (
        <p className={s.error}>{error}</p>
      ) : invalid ? (
        <p className={s.note}>{invalid}</p>
      ) : preview ? (
        <form className={s.form} onSubmit={onSubmit}>
          <div className={s.meta}>
            {preview.email}
            <Badge appearance="tint" color="brand">
              {preview.role}
            </Badge>
          </div>
          {preview.needs_account && (
            <>
              <Field label="Full name">
                <Input value={name} onChange={(_, d) => setName(d.value)} autoComplete="name" />
              </Field>
              <Field label="Create a password" hint="At least 8 characters.">
                <Input
                  type="password"
                  value={password}
                  onChange={(_, d) => setPassword(d.value)}
                  required
                  autoComplete="new-password"
                />
              </Field>
            </>
          )}
          {error && <span className={s.error}>{error}</span>}
          <Button type="submit" appearance="primary" className={s.submit} disabled={busy}>
            {busy ? "Joining…" : `Join ${preview.workspace}`}
          </Button>
        </form>
      ) : null}
    </AuthShell>
  );
}
