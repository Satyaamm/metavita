"use client";

import { Caption1, makeStyles } from "@fluentui/react-components";
import { scaleBars } from "@/lib/chart";
import { appTokens, palette } from "../app/theme";

const useStyles = makeStyles({
  root: { display: "flex", flexDirection: "column", gap: "8px" },
  bars: { display: "flex", alignItems: "flex-end", gap: "4px", height: "140px" },
  bar: {
    flex: 1,
    minWidth: "4px",
    borderRadius: "4px 4px 0 0",
    background: `linear-gradient(180deg, ${palette.brandPrimary}, #8B5BE6)`,
    transitionProperty: "height",
    transitionDuration: "200ms",
  },
  empty: { flex: 1, borderRadius: "4px 4px 0 0", backgroundColor: appTokens.border, minHeight: "2px" },
  labels: { display: "flex", justifyContent: "space-between", color: palette.inkSubtle },
});

export interface BarDatum {
  label: string;
  value: number;
}

export function BarChart({ data }: { data: BarDatum[] }) {
  const styles = useStyles();
  const heights = scaleBars(
    data.map((d) => d.value),
    132,
  );

  return (
    <div className={styles.root}>
      <div className={styles.bars}>
        {data.map((d, i) =>
          d.value > 0 ? (
            <div
              key={d.label}
              className={styles.bar}
              style={{ height: `${Math.max(heights[i], 3)}px` }}
              title={`${d.label}: ${d.value}`}
            />
          ) : (
            <div key={d.label} className={styles.empty} title={`${d.label}: 0`} />
          ),
        )}
      </div>
      <div className={styles.labels}>
        <Caption1>{data[0]?.label}</Caption1>
        <Caption1>{data[data.length - 1]?.label}</Caption1>
      </div>
    </div>
  );
}
