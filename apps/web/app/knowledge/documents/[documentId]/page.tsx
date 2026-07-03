"use client";

import { Badge, Caption1, Text, makeStyles } from "@fluentui/react-components";
import { ArrowLeftRegular } from "@fluentui/react-icons";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect } from "react";
import { PageHeader } from "@/components/PageHeader";
import { ChunkListSkeleton } from "@/components/Skeletons";
import { StatusBadge } from "@/components/StatusBadge";
import { useDocDetailStore } from "@/lib/stores/knowledge";
import { appTokens, palette, tints } from "../../../theme";

const useStyles = makeStyles({
  back: { display: "inline-flex", alignItems: "center", gap: "6px", color: palette.inkSubtle, textDecoration: "none" },
  metaRow: { display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" },
  chunk: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  chunkHead: { display: "flex", alignItems: "center", gap: "8px" },
  pill: {
    background: `linear-gradient(135deg, ${tints.lilac}, ${tints.sky})`,
    color: palette.brandPrimary,
    borderRadius: "999px",
    padding: "2px 10px",
    fontSize: "12px",
    fontWeight: 600,
  },
  text: {
    whiteSpace: "pre-wrap",
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
    fontSize: "13px",
    lineHeight: 1.55,
    color: palette.ink,
  },
  list: { display: "flex", flexDirection: "column", gap: "12px" },
});

export default function DocumentDetailPage() {
  const styles = useStyles();
  const { documentId } = useParams<{ documentId: string }>();
  const { doc, chunks, status, error, fetch } = useDocDetailStore();

  useEffect(() => {
    fetch(documentId);
  }, [documentId, fetch]);

  return (
    <>
      <Link href="/knowledge/documents" className={styles.back}>
        <ArrowLeftRegular /> Documents
      </Link>

      <PageHeader
        title={doc?.filename ?? "Document"}
        description="Chunk inspector — exactly how this document was split for retrieval."
      />

      {error && <Text style={{ color: palette.danger }}>{error}</Text>}

      {doc && (
        <div className={styles.metaRow}>
          <StatusBadge status={doc.status} />
          <Badge appearance="tint" color="informative">
            {doc.chunk_count ?? chunks.length} chunks
          </Badge>
          {doc.content_type && (
            <Caption1 style={{ color: palette.inkSubtle }}>{doc.content_type}</Caption1>
          )}
        </div>
      )}

      {(status === "idle" || status === "loading") && <ChunkListSkeleton count={4} />}

      {status === "ready" && chunks.length === 0 && (
        <Text style={{ color: palette.inkSubtle }}>No chunks for this document.</Text>
      )}

      {status === "ready" && chunks.length > 0 && (
        <div className={styles.list}>
          {chunks.map((c) => (
            <div key={c.chunk_index} className={styles.chunk}>
              <div className={styles.chunkHead}>
                <span className={styles.pill}>#{c.chunk_index}</span>
                <Caption1 style={{ color: palette.inkSubtle }}>{c.text.length} chars</Caption1>
              </div>
              <div className={styles.text}>{c.text}</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
