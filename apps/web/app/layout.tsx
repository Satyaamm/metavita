import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppShell } from "../components/AppShell";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "MetaVita",
  description: "Agentic RAG platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0 }}>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
