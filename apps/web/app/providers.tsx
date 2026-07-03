"use client";

import { FluentProvider } from "@fluentui/react-components";
import type { ReactNode } from "react";
import { metavitaLightTheme } from "./theme";

export function Providers({ children }: { children: ReactNode }) {
  return <FluentProvider theme={metavitaLightTheme}>{children}</FluentProvider>;
}
