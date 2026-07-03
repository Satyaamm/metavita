"use client";

import {
  Badge,
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  DialogTrigger,
  Dropdown,
  Field,
  Input,
  MessageBar,
  MessageBarActions,
  MessageBarBody,
  Option,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import {
  CopyRegular,
  DeleteRegular,
  PersonAddRegular,
  SendRegular,
} from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect, useState } from "react";
import { TableSkeleton } from "@/components/Skeletons";
import { ApiError, type InviteItem, api } from "@/lib/api";
import { useMembersStore } from "@/lib/stores/settings";
import { appTokens, palette } from "../../theme";

const INVITE_ROLES = ["admin", "editor", "viewer"];

const useStyles = makeStyles({
  toolbar: { display: "flex", justifyContent: "flex-end" },
  section: { display: "flex", flexDirection: "column", gap: "10px" },
  heading: { fontWeight: 600, fontSize: "14px", color: palette.ink },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    overflow: "hidden",
  },
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "380px" },
  muted: { color: palette.inkSubtle, fontSize: "13px" },
  rowActions: { display: "flex", gap: "4px", justifyContent: "flex-end" },
});

export default function MembersPage() {
  const styles = useStyles();
  const { items, status, fetch, remove } = useMembersStore();
  const [invites, setInvites] = useState<InviteItem[]>([]);
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [error, setError] = useState<string | null>(null);
  const [noEmailConn, setNoEmailConn] = useState(false);
  const [busy, setBusy] = useState(false);

  async function loadInvites() {
    try {
      const res = await api.listInvites();
      setInvites(res.items.filter((i) => i.status === "pending"));
    } catch {
      /* non-fatal */
    }
  }

  useEffect(() => {
    fetch();
    loadInvites();
  }, [fetch]);

  async function submit() {
    setBusy(true);
    setError(null);
    setNoEmailConn(false);
    try {
      await api.createInvite(email, role);
      setOpen(false);
      setEmail("");
      await loadInvites();
    } catch (e) {
      if (e instanceof ApiError && e.status === 400) {
        setNoEmailConn(true);
      } else if (e instanceof ApiError && e.status === 409) {
        setError("That person is already a member.");
      } else if (e instanceof ApiError && e.status === 403) {
        setError("You need an admin or owner role to invite members.");
      } else {
        setError("Could not send the invitation. Please try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function copyLink(url: string) {
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      /* clipboard blocked — ignore */
    }
  }

  return (
    <>
      <div className={styles.toolbar}>
        <Dialog open={open} onOpenChange={(_, d) => setOpen(d.open)}>
          <DialogTrigger disableButtonEnhancement>
            <Button appearance="primary" icon={<PersonAddRegular />}>
              Invite member
            </Button>
          </DialogTrigger>
          <DialogSurface>
            <DialogBody>
              <DialogTitle>Invite a member</DialogTitle>
              <DialogContent>
                <div className={styles.form}>
                  <Text className={styles.muted}>
                    We&apos;ll email an invitation link through your workspace&apos;s email
                    provider. They set their own password when they accept.
                  </Text>
                  <Field label="Email" required>
                    <Input
                      type="email"
                      value={email}
                      onChange={(_, d) => setEmail(d.value)}
                      placeholder="teammate@company.com"
                    />
                  </Field>
                  <Field label="Role">
                    <Dropdown
                      value={role}
                      selectedOptions={[role]}
                      onOptionSelect={(_, d) => setRole(d.optionValue as string)}
                    >
                      {INVITE_ROLES.map((r) => (
                        <Option key={r} value={r}>
                          {r}
                        </Option>
                      ))}
                    </Dropdown>
                  </Field>
                  {noEmailConn && (
                    <MessageBar intent="warning">
                      <MessageBarBody>
                        Connect an email provider (SMTP, Resend, SendGrid, Mailgun, Postmark,
                        or SES) before inviting — invites are sent through your own provider.
                      </MessageBarBody>
                      <MessageBarActions>
                        <Link href="/connections">
                          <Button size="small">Go to Connections</Button>
                        </Link>
                      </MessageBarActions>
                    </MessageBar>
                  )}
                  {error && (
                    <MessageBar intent="error">
                      <MessageBarBody>{error}</MessageBarBody>
                    </MessageBar>
                  )}
                </div>
              </DialogContent>
              <DialogActions>
                <DialogTrigger disableButtonEnhancement>
                  <Button appearance="secondary">Cancel</Button>
                </DialogTrigger>
                <Button
                  appearance="primary"
                  icon={<SendRegular />}
                  onClick={submit}
                  disabled={busy || !email}
                >
                  {busy ? "Sending…" : "Send invite"}
                </Button>
              </DialogActions>
            </DialogBody>
          </DialogSurface>
        </Dialog>
      </div>

      {/* Pending invites */}
      {invites.length > 0 && (
        <div className={styles.section}>
          <span className={styles.heading}>Pending invitations</span>
          <div className={styles.card}>
            <Table aria-label="Pending invitations">
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Email</TableHeaderCell>
                  <TableHeaderCell>Role</TableHeaderCell>
                  <TableHeaderCell>Invited by</TableHeaderCell>
                  <TableHeaderCell />
                </TableRow>
              </TableHeader>
              <TableBody>
                {invites.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.email}</TableCell>
                    <TableCell>
                      <Badge appearance="tint" color="brand">
                        {inv.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className={styles.muted}>{inv.invited_by || "—"}</span>
                    </TableCell>
                    <TableCell>
                      <div className={styles.rowActions}>
                        <Button
                          size="small"
                          appearance="subtle"
                          icon={<CopyRegular />}
                          onClick={() => copyLink(inv.accept_url)}
                          aria-label="Copy invite link"
                        />
                        <Button
                          size="small"
                          appearance="subtle"
                          icon={<SendRegular />}
                          onClick={() => api.resendInvite(inv.id).catch(() => {})}
                          aria-label="Resend invite"
                        />
                        <Button
                          size="small"
                          appearance="subtle"
                          icon={<DeleteRegular />}
                          onClick={async () => {
                            await api.revokeInvite(inv.id).catch(() => {});
                            await loadInvites();
                          }}
                          aria-label="Revoke invite"
                        />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {/* Members */}
      <div className={styles.section}>
        <span className={styles.heading}>Members</span>
        {(status === "idle" || status === "loading") && <TableSkeleton rows={4} />}
        {status === "ready" && (
          <div className={styles.card}>
            <Table aria-label="Members">
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Name</TableHeaderCell>
                  <TableHeaderCell>Email</TableHeaderCell>
                  <TableHeaderCell>Role</TableHeaderCell>
                  <TableHeaderCell />
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((m) => (
                  <TableRow key={m.membership_id}>
                    <TableCell>{m.user.name}</TableCell>
                    <TableCell>{m.user.email}</TableCell>
                    <TableCell>
                      <Badge appearance="tint" color={m.role === "owner" ? "brand" : "subtle"}>
                        {m.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className={styles.rowActions}>
                        {m.role !== "owner" && (
                          <Button
                            size="small"
                            appearance="subtle"
                            icon={<DeleteRegular />}
                            onClick={() => remove(m.membership_id)}
                            aria-label="Remove member"
                          />
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </>
  );
}
