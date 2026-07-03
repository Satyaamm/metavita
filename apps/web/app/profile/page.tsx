"use client";

import {
  Avatar,
  Badge,
  Button,
  Caption1,
  Spinner,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import {
  BuildingRegular,
  PersonRegular,
  SignOutRegular,
} from "@fluentui/react-icons";
import Link from "next/link";
import { useEffect } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSessionStore, signOut } from "@/lib/stores/session";
import { useWorkspaceStore } from "@/lib/stores/settings";
import { appTokens, palette, tints } from "../theme";

const useStyles = makeStyles({
  grid: { display: "grid", gap: "16px", maxWidth: "640px" },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "22px",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  },
  head: { display: "flex", alignItems: "center", gap: "8px" },
  iconChip: {
    width: "34px",
    height: "34px",
    borderRadius: "10px",
    background: `linear-gradient(135deg, ${tints.lilac}, ${tints.sky})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
  },
  accountRow: { display: "flex", alignItems: "center", gap: "16px" },
  field: { display: "flex", flexDirection: "column", gap: "2px" },
  label: { color: palette.inkSubtle, textTransform: "uppercase", letterSpacing: "0.05em", fontSize: "10px" },
  mono: { fontFamily: "ui-monospace, Menlo, monospace", color: palette.inkSubtle },
  actions: { display: "flex", justifyContent: "flex-end" },
});

export default function ProfilePage() {
  const styles = useStyles();
  const { me, status, fetch } = useSessionStore();
  const workspace = useWorkspaceStore((s) => s.workspace);
  const fetchWorkspace = useWorkspaceStore((s) => s.fetch);

  useEffect(() => {
    fetch();
    fetchWorkspace();
  }, [fetch, fetchWorkspace]);

  const wsName = me?.workspace?.name ?? workspace?.name ?? "Default workspace";

  return (
    <>
      <PageHeader title="Profile" description="Your account and the workspace you're working in." />

      {status === "idle" || status === "loading" ? (
        <Spinner label="Loading your profile…" />
      ) : (
        <div className={styles.grid}>
          {/* Account */}
          <div className={styles.card}>
            <div className={styles.head}>
              <span className={styles.iconChip}>
                <PersonRegular />
              </span>
              <Text weight="semibold">Account</Text>
            </div>

            {me ? (
              <div className={styles.accountRow}>
                <Avatar name={me.user.name} color="colorful" size={56} />
                <div className={styles.field}>
                  <Text weight="semibold" size={400}>
                    {me.user.name}
                  </Text>
                  <Caption1 style={{ color: palette.inkSubtle }}>{me.user.email}</Caption1>
                  <Badge appearance="tint" color="brand" style={{ alignSelf: "flex-start", marginTop: 4 }}>
                    Owner
                  </Badge>
                </div>
              </div>
            ) : (
              <div className={styles.field}>
                <Text>You&apos;re using MetaVita&apos;s default workspace.</Text>
                <Caption1 style={{ color: palette.inkSubtle }}>
                  Sign-in isn&apos;t enabled in this environment yet, so there&apos;s no personal
                  account to show. Once auth is on, your name, email, and role appear here.
                </Caption1>
              </div>
            )}
          </div>

          {/* Workspace */}
          <div className={styles.card}>
            <div className={styles.head}>
              <span className={styles.iconChip}>
                <BuildingRegular />
              </span>
              <Text weight="semibold">Workspace</Text>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Name</span>
              <Text>{wsName}</Text>
            </div>
            {workspace?.id && (
              <div className={styles.field}>
                <span className={styles.label}>Workspace ID</span>
                <Caption1 className={styles.mono}>{workspace.id}</Caption1>
              </div>
            )}
            <div className={styles.field}>
              <span className={styles.label}>Key policy</span>
              <Text>{workspace?.key_policy ?? "platform"}</Text>
            </div>
            <div className={styles.actions}>
              <Link href="/settings">
                <Button appearance="secondary">Manage workspace settings</Button>
              </Link>
            </div>
          </div>

          <div className={styles.actions}>
            <Button appearance="subtle" icon={<SignOutRegular />} onClick={signOut}>
              Sign out
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
