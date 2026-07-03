"use client";

import { Text, Title3, makeStyles } from "@fluentui/react-components";
import type { ReactNode } from "react";
import { palette } from "../app/theme";

const useStyles = makeStyles({
  root: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "16px",
    marginBottom: "4px",
  },
  left: { display: "flex", flexDirection: "column", gap: "4px" },
  desc: { color: palette.inkSubtle, maxWidth: "640px" },
  actions: { display: "flex", gap: "10px", flexShrink: 0 },
});

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  const styles = useStyles();
  return (
    <div className={styles.root}>
      <div className={styles.left}>
        <Title3>{title}</Title3>
        {description && <Text className={styles.desc}>{description}</Text>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </div>
  );
}
