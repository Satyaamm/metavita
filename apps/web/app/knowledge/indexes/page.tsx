"use client";

import {
  Badge,
  Button,
  Caption1,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  DialogTrigger,
  Dropdown,
  Field,
  Input,
  Option,
  Text,
  makeStyles,
} from "@fluentui/react-components";
import { AddRegular, LayerRegular } from "@fluentui/react-icons";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { CardGridSkeleton } from "@/components/Skeletons";
import type { Modality } from "@/lib/api";
import { useIndexesStore } from "@/lib/stores/knowledge";
import { appTokens, palette, tints } from "../../theme";

const useStyles = makeStyles({
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px" },
  card: {
    backgroundColor: appTokens.surfaceBg,
    border: `1px solid ${appTokens.border}`,
    borderRadius: appTokens.radiusCard,
    boxShadow: appTokens.shadowCard,
    padding: "18px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  top: { display: "flex", alignItems: "center", gap: "10px" },
  icon: {
    width: "38px",
    height: "38px",
    borderRadius: "11px",
    background: `linear-gradient(135deg, ${tints.sage}, ${tints.sky})`,
    color: palette.brandPrimary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "19px",
  },
  meta: { color: palette.inkSubtle },
  badges: { display: "flex", gap: "6px", flexWrap: "wrap" },
  form: { display: "flex", flexDirection: "column", gap: "12px", minWidth: "420px" },
});

const MODALITIES: Modality[] = ["text", "image", "audio", "video"];
const PROVIDERS = ["openai", "ollama", "azure"];

export default function IndexesPage() {
  const styles = useStyles();
  const { items, status, fetch, create } = useIndexesStore();
  const [open, setOpen] = useState(false);

  const [name, setName] = useState("");
  const [modality, setModality] = useState<Modality>("text");
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("text-embedding-3-small");
  const [chunkSize, setChunkSize] = useState("1200");
  const [overlap, setOverlap] = useState("150");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch();
  }, [fetch]);

  async function submit() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await create({
        name,
        modality,
        embedding_provider: provider,
        embedding_model: model,
        chunk_size: Number(chunkSize) || 1200,
        overlap: Number(overlap) || 150,
      });
      setOpen(false);
      setName("");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Indexes"
        description="Group sources into a retrievable index. Each index pins a modality, embedding model, and chunking."
        actions={
          <Dialog open={open} onOpenChange={(_, d) => setOpen(d.open)}>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="primary" icon={<AddRegular />}>
                New index
              </Button>
            </DialogTrigger>
            <DialogSurface>
              <DialogBody>
                <DialogTitle>New index</DialogTitle>
                <DialogContent>
                  <div className={styles.form}>
                    <Field label="Name" required>
                      <Input value={name} onChange={(_, d) => setName(d.value)} placeholder="Product docs" />
                    </Field>
                    <Field label="Modality">
                      <Dropdown
                        value={modality}
                        selectedOptions={[modality]}
                        onOptionSelect={(_, d) => setModality(d.optionValue as Modality)}
                      >
                        {MODALITIES.map((m) => (
                          <Option key={m} value={m}>
                            {m}
                          </Option>
                        ))}
                      </Dropdown>
                    </Field>
                    <Field label="Embedding provider">
                      <Dropdown
                        value={provider}
                        selectedOptions={[provider]}
                        onOptionSelect={(_, d) => setProvider(d.optionValue as string)}
                      >
                        {PROVIDERS.map((p) => (
                          <Option key={p} value={p}>
                            {p}
                          </Option>
                        ))}
                      </Dropdown>
                    </Field>
                    <Field label="Embedding model">
                      <Input value={model} onChange={(_, d) => setModel(d.value)} />
                    </Field>
                    <Field label="Chunk size">
                      <Input type="number" value={chunkSize} onChange={(_, d) => setChunkSize(d.value)} />
                    </Field>
                    <Field label="Overlap">
                      <Input type="number" value={overlap} onChange={(_, d) => setOverlap(d.value)} />
                    </Field>
                  </div>
                </DialogContent>
                <DialogActions>
                  <DialogTrigger disableButtonEnhancement>
                    <Button appearance="secondary">Cancel</Button>
                  </DialogTrigger>
                  <Button appearance="primary" onClick={submit} disabled={saving || !name}>
                    {saving ? "Creating…" : "Create index"}
                  </Button>
                </DialogActions>
              </DialogBody>
            </DialogSurface>
          </Dialog>
        }
      />

      {(status === "idle" || status === "loading") && <CardGridSkeleton count={3} />}

      {status === "ready" && items.length === 0 && (
        <EmptyState
          icon={<LayerRegular />}
          title="No indexes yet"
          description="Create an index to choose an embedder (text or video) and make your sources retrievable."
        />
      )}

      {status === "ready" && items.length > 0 && (
        <div className={styles.grid}>
          {items.map((i) => (
            <div key={i.id} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.icon}>
                  <LayerRegular />
                </span>
                <Text weight="semibold">{i.name}</Text>
              </div>
              <div className={styles.badges}>
                <Badge appearance="tint" color="brand">
                  {i.modality}
                </Badge>
                <Badge appearance="tint" color="informative">
                  {i.embedding_provider}
                </Badge>
                <Badge appearance="tint" color="subtle">
                  dim {i.embedding_dim}
                </Badge>
              </div>
              <Caption1 className={styles.meta}>{i.embedding_model}</Caption1>
              <Caption1 className={styles.meta}>
                chunk {i.chunk_size} · overlap {i.overlap}
              </Caption1>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
