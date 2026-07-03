# Provider logos (drop-in overrides)

`ProviderLogo` resolves a provider's mark in this order:

1. **@lobehub/icons** — AI model providers (OpenAI, Anthropic, Azure, AWS/Bedrock,
   GCP/Vertex, Mistral, Cohere, Groq, Together, OpenRouter, Ollama, Voyage, Jina).
2. **simple-icons** — Qdrant, Milvus, pgvector (Postgres mark), Mailgun, Resend.
3. **`public/logos/<provider>.svg`** — drop an official SVG here and it's used
   automatically (no code change).
4. Branded monogram fallback.

## Add an official logo

Save the vendor's official SVG (from their brand / press kit) as the provider key:

```
public/logos/pinecone.svg
public/logos/weaviate.svg
public/logos/chroma.svg
public/logos/moss.svg
```

The provider key matches the catalog (`provider` field): `pinecone`, `weaviate`,
`chroma`, `moss`, `twelvelabs`, `minio`, `s3`, `gcs`, `azure_blob`, etc.

These four currently show a monogram because no maintained open-source icon set
ships them — add the official SVGs to make them real logos.
