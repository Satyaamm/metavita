"use client";

import { Skeleton, SkeletonItem, makeStyles } from "@fluentui/react-components";
import { appTokens } from "../app/theme";

const useStyles = makeStyles({
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
    gap: "16px",
  },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    padding: "18px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  rowCard: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    overflow: "hidden",
  },
  row: {
    display: "grid",
    gridTemplateColumns: "2fr 1fr 1fr 1fr",
    gap: "16px",
    alignItems: "center",
    padding: "14px 16px",
    borderBottom: `1px solid ${appTokens.border}`,
  },
  block: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  stack: { display: "flex", flexDirection: "column", gap: "12px" },
  iconRow: { display: "flex", alignItems: "center", gap: "12px" },
});

function range(n: number) {
  return Array.from({ length: n }, (_, i) => i);
}

export function CardGridSkeleton({ count = 6 }: { count?: number }) {
  const s = useStyles();
  return (
    <div className={s.grid}>
      {range(count).map((i) => (
        <div key={i} className={s.card}>
          <Skeleton>
            <div className={s.iconRow}>
              <SkeletonItem shape="square" size={40} style={{ flexShrink: 0 }} />
              <SkeletonItem style={{ width: "60%" }} />
            </div>
          </Skeleton>
          <Skeleton>
            <SkeletonItem style={{ width: "80%" }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem style={{ width: "40%" }} />
          </Skeleton>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  const s = useStyles();
  return (
    <div className={s.rowCard}>
      {range(rows).map((i) => (
        <div key={i} className={s.row}>
          <Skeleton>
            <SkeletonItem style={{ width: "70%" }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem style={{ width: "50%" }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem style={{ width: "50%" }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem style={{ width: "60%" }} />
          </Skeleton>
        </div>
      ))}
    </div>
  );
}

export function ChunkListSkeleton({ count = 4 }: { count?: number }) {
  const s = useStyles();
  return (
    <div className={s.stack}>
      {range(count).map((i) => (
        <div key={i} className={s.block}>
          <Skeleton>
            <SkeletonItem style={{ width: "20%" }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem />
          </Skeleton>
          <Skeleton>
            <SkeletonItem style={{ width: "90%" }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem style={{ width: "75%" }} />
          </Skeleton>
        </div>
      ))}
    </div>
  );
}
