"use client";

import { Button, Caption1, Dropdown, Option, makeStyles, tokens } from "@fluentui/react-components";
import { ChevronLeftRegular, ChevronRightRegular } from "@fluentui/react-icons";
import { PAGE_SIZES, itemRange, pageCount, pageWindow } from "@/lib/pagination";

const useStyles = makeStyles({
  root: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px",
    flexWrap: "wrap",
    paddingTop: "4px",
  },
  left: { display: "flex", alignItems: "center", gap: "10px" },
  pages: { display: "flex", alignItems: "center", gap: "4px" },
  pageBtn: { minWidth: "32px" },
  current: { backgroundColor: tokens.colorBrandBackground2, color: tokens.colorBrandForeground1 },
  muted: { color: tokens.colorNeutralForeground3 },
});

export interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

export function Pagination({ page, pageSize, total, onPageChange, onPageSizeChange }: PaginationProps) {
  const styles = useStyles();
  const pages = pageCount(total, pageSize);
  const { from, to } = itemRange(page, pageSize, total);
  const window = pageWindow(page, pages, 2);

  if (total === 0) return null;

  return (
    <div className={styles.root}>
      <div className={styles.left}>
        <Caption1 className={styles.muted}>
          {from}–{to} of {total}
        </Caption1>
        {onPageSizeChange && (
          <Dropdown
            size="small"
            value={`${pageSize} / page`}
            selectedOptions={[String(pageSize)]}
            onOptionSelect={(_, d) => onPageSizeChange(Number(d.optionValue))}
            style={{ minWidth: "110px" }}
          >
            {PAGE_SIZES.map((s) => (
              <Option key={s} value={String(s)} text={`${s} / page`}>
                {`${s} / page`}
              </Option>
            ))}
          </Dropdown>
        )}
      </div>

      <div className={styles.pages}>
        <Button
          size="small"
          appearance="subtle"
          icon={<ChevronLeftRegular />}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        />
        {window[0] > 1 && <Caption1 className={styles.muted}>…</Caption1>}
        {window.map((p) => (
          <Button
            key={p}
            size="small"
            className={`${styles.pageBtn} ${p === page ? styles.current : ""}`}
            appearance={p === page ? "primary" : "subtle"}
            onClick={() => onPageChange(p)}
          >
            {p}
          </Button>
        ))}
        {window[window.length - 1] < pages && <Caption1 className={styles.muted}>…</Caption1>}
        <Button
          size="small"
          appearance="subtle"
          icon={<ChevronRightRegular />}
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        />
      </div>
    </div>
  );
}
