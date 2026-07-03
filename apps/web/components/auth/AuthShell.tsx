"use client";

import { Text, makeStyles } from "@fluentui/react-components";
import type { ReactNode } from "react";
import { Logo } from "../Logo";

const useStyles = makeStyles({
  root: {
    position: "fixed",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
    overflow: "hidden",
    background:
      "radial-gradient(1200px 600px at 15% -10%, #241a4d 0%, transparent 55%)," +
      "radial-gradient(1000px 700px at 110% 20%, #10233f 0%, transparent 50%)," +
      "linear-gradient(160deg, #0a0b16 0%, #0d1024 55%, #0a0b16 100%)",
  },
  // Floating aurora blobs behind the card.
  blobs: { position: "absolute", inset: 0, filter: "blur(60px)", opacity: 0.55 },
  blob: {
    position: "absolute",
    borderRadius: "50%",
    animationIterationCount: "infinite",
    animationTimingFunction: "ease-in-out",
  },
  blobA: {
    width: "440px",
    height: "440px",
    top: "-120px",
    left: "8%",
    background: "radial-gradient(circle at 30% 30%, #7c6bf0, transparent 65%)",
    animationName: {
      "0%,100%": { transform: "translate(0,0) scale(1)" },
      "50%": { transform: "translate(60px,50px) scale(1.18)" },
    },
    animationDuration: "20s",
  },
  blobB: {
    width: "380px",
    height: "380px",
    bottom: "-100px",
    right: "6%",
    background: "radial-gradient(circle at 40% 40%, #3aa0ff, transparent 65%)",
    animationName: {
      "0%,100%": { transform: "translate(0,0) scale(1)" },
      "50%": { transform: "translate(-50px,-40px) scale(1.12)" },
    },
    animationDuration: "26s",
  },
  blobC: {
    width: "320px",
    height: "320px",
    top: "30%",
    right: "34%",
    background: "radial-gradient(circle at 50% 50%, #b06bf0, transparent 65%)",
    animationName: {
      "0%,100%": { transform: "translate(0,0) scale(1)" },
      "50%": { transform: "translate(40px,-60px) scale(1.2)" },
    },
    animationDuration: "32s",
  },
  // Fine grid overlay for a technical, professional texture.
  grid: {
    position: "absolute",
    inset: 0,
    backgroundImage:
      "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px)," +
      "linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
    backgroundSize: "44px 44px",
    maskImage: "radial-gradient(circle at 50% 40%, #000 0%, transparent 75%)",
  },
  card: {
    position: "relative",
    width: "100%",
    maxWidth: "400px",
    background: "rgba(255,255,255,0.98)",
    borderRadius: "16px",
    boxShadow: "0 24px 70px rgba(0,0,0,0.5)",
    border: "1px solid rgba(255,255,255,0.5)",
    padding: "34px 32px",
    display: "flex",
    flexDirection: "column",
    gap: "22px",
  },
  wide: { maxWidth: "480px" },
  brand: { display: "flex", justifyContent: "center" },
  logoChip: {
    width: "40px",
    height: "40px",
    borderRadius: "11px",
    background: "#16181D",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  heading: { display: "flex", flexDirection: "column", gap: "5px", alignItems: "center" },
  title: { fontSize: "21px", fontWeight: 600, color: "#16181D" },
  subtitle: { color: "#5C6070", fontSize: "13px", textAlign: "center", lineHeight: 1.5 },
  footer: { color: "#5C6070", fontSize: "13px", textAlign: "center" },
});

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
  wide,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
}) {
  const s = useStyles();
  return (
    <div className={s.root}>
      <div className={s.blobs} aria-hidden>
        <span className={`${s.blob} ${s.blobA}`} />
        <span className={`${s.blob} ${s.blobB}`} />
        <span className={`${s.blob} ${s.blobC}`} />
      </div>
      <div className={s.grid} aria-hidden />

      <div className={`${s.card} ${wide ? s.wide : ""}`}>
        <div className={s.brand}>
          <span className={s.logoChip}>
            <Logo size={22} />
          </span>
        </div>
        <div className={s.heading}>
          <span className={s.title}>{title}</span>
          {subtitle && <Text className={s.subtitle}>{subtitle}</Text>}
        </div>
        {children}
        {footer && <div className={s.footer}>{footer}</div>}
      </div>
    </div>
  );
}
