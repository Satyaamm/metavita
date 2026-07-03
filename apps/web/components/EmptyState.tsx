"use client";

import { Body1, Button, Text, makeStyles } from "@fluentui/react-components";
import Link from "next/link";
import type { ReactNode } from "react";
import { appTokens, palette } from "../app/theme";

const useStyles = makeStyles({
  root: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "56px 32px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
    gap: "10px",
  },
  iconWrap: {
    width: "56px",
    height: "56px",
    borderRadius: "16px",
    backgroundColor: palette.brandSoft,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "26px",
    marginBottom: "6px",
  },
  desc: { color: palette.inkSubtle, maxWidth: "440px" },
  actions: { display: "flex", gap: "10px", marginTop: "10px" },
});

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  actionHref,
  secondary,
}: {
  icon: ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
  secondary?: ReactNode;
}) {
  const styles = useStyles();
  return (
    <div className={styles.root}>
      <div className={styles.iconWrap}>{icon}</div>
      <Text weight="semibold" size={400}>
        {title}
      </Text>
      {description && <Body1 className={styles.desc}>{description}</Body1>}
      {(actionLabel || secondary) && (
        <div className={styles.actions}>
          {actionLabel && actionHref && (
            <Link href={actionHref}>
              <Button appearance="primary">{actionLabel}</Button>
            </Link>
          )}
          {secondary}
        </div>
      )}
    </div>
  );
}
