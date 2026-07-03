"use client";

import { Badge, type BadgeProps } from "@fluentui/react-components";

const MAP: Record<string, BadgeProps["color"]> = {
  indexed: "success",
  active: "success",
  pending: "warning",
  syncing: "informative",
  error: "danger",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge appearance="tint" color={MAP[status] ?? "subtle"}>
      {status}
    </Badge>
  );
}
