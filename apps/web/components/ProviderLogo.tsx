"use client";

/**
 * Official provider logos. AI vendors use @lobehub/icons (MIT brand-icon set —
 * the real OpenAI / Anthropic / Azure / AWS / GCP / Mistral / Cohere / … marks).
 * We import each brand's pure glyph (Color where the brand has one, else its
 * monochrome mark) to avoid the package's heavier `features` bundle. Services
 * lobe doesn't cover (most vector DBs) fall back to a tidy monogram.
 */
import Anthropic from "@lobehub/icons/es/Anthropic/components/Mono";
import Aws from "@lobehub/icons/es/Aws/components/Color";
import Azure from "@lobehub/icons/es/Azure/components/Color";
import AzureAI from "@lobehub/icons/es/AzureAI/components/Color";
import Bedrock from "@lobehub/icons/es/Bedrock/components/Color";
import Cohere from "@lobehub/icons/es/Cohere/components/Color";
import GoogleCloud from "@lobehub/icons/es/GoogleCloud/components/Color";
import Groq from "@lobehub/icons/es/Groq/components/Mono";
import Jina from "@lobehub/icons/es/Jina/components/Mono";
import Mistral from "@lobehub/icons/es/Mistral/components/Color";
import Ollama from "@lobehub/icons/es/Ollama/components/Mono";
import OpenAI from "@lobehub/icons/es/OpenAI/components/Mono";
import OpenRouter from "@lobehub/icons/es/OpenRouter/components/Mono";
import Together from "@lobehub/icons/es/Together/components/Color";
import VertexAI from "@lobehub/icons/es/VertexAI/components/Color";
import Voyage from "@lobehub/icons/es/Voyage/components/Color";
// Vector DBs aren't in lobe — use simple-icons' real brand marks where they exist.
import { siMailgun, siMilvus, siPostgresql, siQdrant, siResend } from "simple-icons";
import { type ComponentType, useState } from "react";

type Glyph = ComponentType<{ size?: number | string }>;
type SimpleIcon = { path: string; hex: string; title: string };

const SIMPLE: Record<string, SimpleIcon> = {
  qdrant: siQdrant,
  milvus: siMilvus,
  pgvector: siPostgresql, // pgvector is a Postgres extension — use the Postgres mark
  mailgun: siMailgun,
  resend: siResend,
};

function SimpleSvg({ icon, size }: { icon: SimpleIcon; size: number }) {
  return (
    <svg role="img" viewBox="0 0 24 24" width={size} height={size} aria-label={icon.title}>
      <path d={icon.path} fill={`#${icon.hex}`} />
    </svg>
  );
}

const MAP: Record<string, Glyph> = {
  // llm
  anthropic: Anthropic,
  openai: OpenAI,
  openai_compatible: OpenAI,
  azure_openai: AzureAI,
  aws_bedrock: Bedrock,
  gcp_vertex: VertexAI,
  mistral: Mistral,
  groq: Groq,
  together: Together,
  openrouter: OpenRouter,
  ollama: Ollama,
  // embeddings / rerank
  cohere: Cohere,
  voyage: Voyage,
  jina: Jina,
  // video
  azure_video: AzureAI,
  aws_rekognition: Aws,
  gcp_video_intelligence: GoogleCloud,
  // object store
  s3: Aws,
  gcs: GoogleCloud,
  azure_blob: Azure,
  // email
  ses: Aws,
};

const MONOGRAM_BG: Record<string, string> = {
  pinecone: "#1B17F5",
  qdrant: "#DC244C",
  weaviate: "#00C9A7",
  chroma: "#327EFF",
  milvus: "#00A1EA",
  moss: "#3B7A57",
  pgvector: "#336791",
  twelvelabs: "#1A1A2E",
  minio: "#C72E49",
  sendgrid: "#1A82E2",
  postmark: "#FFCE00",
  smtp: "#5B5BD6",
};

function initials(s: string): string {
  return s.replace(/[^a-zA-Z]/g, "").slice(0, 2).toUpperCase() || "?";
}

export function ProviderLogo({
  provider,
  label,
  size = 28,
}: {
  provider: string;
  label?: string;
  size?: number;
}) {
  const Icon = MAP[provider];
  if (Icon) return <Icon size={size} />;
  const simple = SIMPLE[provider];
  if (simple) return <SimpleSvg icon={simple} size={size} />;
  // Drop an official SVG at public/logos/<provider>.svg and it's used automatically;
  // otherwise fall back to a branded monogram.
  return <LocalOrMonogram provider={provider} label={label} size={size} />;
}

function LocalOrMonogram({
  provider,
  label,
  size,
}: {
  provider: string;
  label?: string;
  size: number;
}) {
  const [failed, setFailed] = useState(false);
  if (!failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={`/logos/${provider}.svg`}
        alt={label || provider}
        width={size}
        height={size}
        style={{ objectFit: "contain" }}
        onError={() => setFailed(true)}
      />
    );
  }
  const bg = MONOGRAM_BG[provider] ?? "#5B5BD6";
  return (
    <span
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.28),
        background: bg,
        color: "#fff",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: Math.round(size * 0.42),
        fontWeight: 700,
        lineHeight: 1,
      }}
    >
      {initials(provider || label || "?")}
    </span>
  );
}
