/**
 * Centralized list side-effects — renders the right branch for an async list:
 * skeleton while loading, an error line on failure, an empty state when there's
 * no data, otherwise the content followed by the pagination footer. Removes the
 * repeated `status === …` branching from every list page.
 */
import { Text } from "@fluentui/react-components";
import type { ReactNode } from "react";
import type { AsyncStatus } from "@/lib/stores/knowledge";
import { palette } from "../app/theme";

interface ListViewProps {
  status: AsyncStatus;
  isEmpty: boolean;
  skeleton: ReactNode;
  empty: ReactNode;
  error?: string;
  footer?: ReactNode; // typically <Pagination />
  children: ReactNode;
}

export function ListView({
  status,
  isEmpty,
  skeleton,
  empty,
  error,
  footer,
  children,
}: ListViewProps) {
  if (status === "idle" || status === "loading") return <>{skeleton}</>;
  if (status === "error") {
    return <Text style={{ color: palette.danger }}>{error ?? "Couldn’t load this list."}</Text>;
  }
  if (isEmpty) return <>{empty}</>;
  return (
    <>
      {children}
      {footer}
    </>
  );
}
