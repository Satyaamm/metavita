"""The integration catalog — every service a user can bring, declared as data.

Add a provider by appending one `Integration(...)`. Capability slots in the builder
and the Connections UI pick these up automatically. No platform defaults are bundled.
"""

from __future__ import annotations

from . import testers as t
from .base import Field, Integration, IntegrationRegistry


def _key(label: str = "API key", ph: str = "") -> Field:
    return Field("api_key", label, type="password", secret=True, placeholder=ph)


def _model(ph: str, required: bool = False) -> Field:
    return Field("model", "Model", required=required, placeholder=ph)


def _base_url(ph: str) -> Field:
    return Field("base_url", "Base URL", required=False, placeholder=ph, help="Override for self-hosted / proxy.")


INTEGRATIONS: list[Integration] = [
    # ───────────────────────── LLM (chat / reasoning) ────────────────────────
    Integration("llm", "anthropic", "Anthropic (Claude)", "Claude models for reasoning & agents.",
        "https://docs.anthropic.com", [_key(ph="sk-ant-…"), _model("claude-opus-4-8")], t.anthropic),
    Integration("llm", "openai", "OpenAI", "GPT models via the OpenAI API.",
        "https://platform.openai.com/docs", [_key(ph="sk-…"), _model("gpt-4o"), _base_url("https://api.openai.com/v1")],
        t.openai_compatible),
    Integration("llm", "azure_openai", "Azure OpenAI", "OpenAI models hosted on Azure.",
        "https://learn.microsoft.com/azure/ai-services/openai/", [
            Field("endpoint", "Endpoint", placeholder="https://my-resource.openai.azure.com"),
            _key(ph="azure key"),
            Field("deployment", "Deployment name", placeholder="gpt-4o"),
            Field("api_version", "API version", required=False, default="2024-06-01"),
        ], t.azure_openai),
    Integration("llm", "aws_bedrock", "AWS Bedrock", "Claude/Titan/Llama via Amazon Bedrock.",
        "https://docs.aws.amazon.com/bedrock/", [
            Field("region", "AWS region", placeholder="us-east-1"),
            Field("access_key_id", "Access key ID", secret=True),
            Field("secret_access_key", "Secret access key", type="password", secret=True),
            _model("anthropic.claude-3-5-sonnet-20240620-v1:0"),
        ]),
    Integration("llm", "gcp_vertex", "Google Vertex AI", "Gemini / Claude on Vertex AI.",
        "https://cloud.google.com/vertex-ai/docs", [
            Field("project_id", "GCP project ID"),
            Field("location", "Location", placeholder="us-central1"),
            Field("service_account_json", "Service account JSON", type="password", secret=True,
                  help="Paste the full service-account key JSON."),
            _model("gemini-1.5-pro"),
        ]),
    Integration("llm", "mistral", "Mistral AI", "Mistral / Mixtral models.",
        "https://docs.mistral.ai", [_key(), _model("mistral-large-latest"),
                                    _base_url("https://api.mistral.ai/v1")], t.openai_compatible),
    Integration("llm", "groq", "Groq", "Fast inference for open models.",
        "https://console.groq.com/docs", [_key(), _model("llama-3.1-70b-versatile"),
                                          _base_url("https://api.groq.com/openai/v1")], t.openai_compatible),
    Integration("llm", "together", "Together AI", "Open models via Together.",
        "https://docs.together.ai", [_key(), _model("meta-llama/Llama-3-70b-chat-hf"),
                                     _base_url("https://api.together.xyz/v1")], t.openai_compatible),
    Integration("llm", "openrouter", "OpenRouter", "One key, many model providers.",
        "https://openrouter.ai/docs", [_key(), _model("anthropic/claude-3.5-sonnet"),
                                       _base_url("https://openrouter.ai/api/v1")], t.openai_compatible),
    Integration("llm", "ollama", "Ollama (local)", "Run open models locally — no key.",
        "https://ollama.com", [_base_url("http://localhost:11434"), _model("llama3.1", required=True)], t.ollama),
    Integration("llm", "openai_compatible", "OpenAI-compatible (custom)", "Any OpenAI-compatible endpoint.",
        "", [Field("base_url", "Base URL", placeholder="https://my-llm.example.com/v1"),
             _key(label="API key (optional)"), _model("my-model", required=True)], t.openai_compatible),

    # ───────────────────────────── Embeddings ────────────────────────────────
    Integration("embeddings", "openai", "OpenAI Embeddings", "text-embedding-3 models.",
        "https://platform.openai.com/docs/guides/embeddings",
        [_key(ph="sk-…"), _model("text-embedding-3-small", required=True), _base_url("https://api.openai.com/v1")],
        t.openai_compatible),
    Integration("embeddings", "azure_openai", "Azure OpenAI Embeddings", "Embeddings on Azure.",
        "https://learn.microsoft.com/azure/ai-services/openai/", [
            Field("endpoint", "Endpoint", placeholder="https://my-resource.openai.azure.com"),
            _key(), Field("deployment", "Deployment name", placeholder="text-embedding-3-small"),
            Field("api_version", "API version", required=False, default="2024-06-01"),
        ], t.azure_openai),
    Integration("embeddings", "cohere", "Cohere Embed", "embed-v3 multilingual embeddings.",
        "https://docs.cohere.com", [_key(), _model("embed-english-v3.0", required=True)], t.cohere),
    Integration("embeddings", "voyage", "Voyage AI", "High-quality retrieval embeddings.",
        "https://docs.voyageai.com", [_key(), _model("voyage-3", required=True)]),
    Integration("embeddings", "jina", "Jina AI", "jina-embeddings models.",
        "https://jina.ai/embeddings", [_key(), _model("jina-embeddings-v3", required=True)]),
    Integration("embeddings", "ollama", "Ollama Embeddings (local)", "Local embeddings — no key.",
        "https://ollama.com", [_base_url("http://localhost:11434"),
                               _model("nomic-embed-text", required=True)], t.ollama),

    # ──────────────────────────── Vector stores ──────────────────────────────
    Integration("vector_store", "pgvector", "pgvector (built-in)", "Postgres + pgvector — the default store.",
        "https://github.com/pgvector/pgvector", [
            Field("dsn", "Postgres DSN", required=False,
                  placeholder="postgresql://… (blank = MetaVita's database)", help="Leave blank to use the platform DB."),
        ]),
    Integration("vector_store", "pinecone", "Pinecone", "Managed serverless vector DB.",
        "https://docs.pinecone.io", [
            _key(ph="pcsk_…"),
            Field("index_host", "Index host", placeholder="my-index-xxxx.svc.region.pinecone.io"),
            Field("namespace", "Namespace", required=False),
        ], t.pinecone),
    Integration("vector_store", "qdrant", "Qdrant", "OSS / cloud vector DB.",
        "https://qdrant.tech/documentation/", [
            Field("url", "URL", placeholder="https://my-cluster.qdrant.io:6333"),
            _key(label="API key (optional)"),
            Field("collection", "Collection", placeholder="metavita"),
        ], t.qdrant),
    Integration("vector_store", "weaviate", "Weaviate", "OSS / cloud, hybrid search.",
        "https://weaviate.io/developers/weaviate", [
            Field("url", "URL", placeholder="https://my-cluster.weaviate.network"),
            _key(label="API key (optional)"),
            Field("class_name", "Class", placeholder="MetaVita"),
        ], t.weaviate),
    Integration("vector_store", "chroma", "Chroma", "Lightweight local/cloud vector DB.",
        "https://docs.trychroma.com", [
            Field("url", "URL", placeholder="http://localhost:8000"),
            Field("collection", "Collection", placeholder="metavita"),
        ], t.chroma),
    Integration("vector_store", "milvus", "Milvus / Zilliz", "Scalable vector DB.",
        "https://milvus.io/docs", [
            Field("uri", "URI", placeholder="https://in01-xxxx.zillizcloud.com"),
            _key(label="Token / API key"),
            Field("collection", "Collection", placeholder="metavita"),
        ]),
    Integration("vector_store", "moss", "Moss", "Sub-10ms semantic search for voice agents & copilots.",
        "https://docs.moss.dev", [
            Field("project_id", "Project ID"),
            _key(label="Project key", ph="moss_access_key_…"),
            Field("index_name", "Index name", default="metavita"),
        ]),

    # ──────────────────────── Video / multimodal ─────────────────────────────
    Integration("video", "azure_video", "Azure AI Vision (video)", "Vectorize & analyze video.",
        "https://learn.microsoft.com/azure/ai-services/computer-vision/", [
            Field("endpoint", "Endpoint", placeholder="https://my-vision.cognitiveservices.azure.com"),
            _key(),
        ]),
    Integration("video", "aws_rekognition", "AWS Rekognition Video", "Detect labels/scenes in video.",
        "https://docs.aws.amazon.com/rekognition/", [
            Field("region", "AWS region", placeholder="us-east-1"),
            Field("access_key_id", "Access key ID", secret=True),
            Field("secret_access_key", "Secret access key", type="password", secret=True),
        ]),
    Integration("video", "gcp_video_intelligence", "Google Video Intelligence", "Analyze video content.",
        "https://cloud.google.com/video-intelligence/docs", [
            Field("project_id", "GCP project ID"),
            Field("service_account_json", "Service account JSON", type="password", secret=True),
        ]),
    Integration("video", "twelvelabs", "TwelveLabs", "Video understanding & embeddings.",
        "https://docs.twelvelabs.io", [_key(), _model("Marengo-retrieval-2.7", required=False)]),

    # ─────────────────────────────── Rerank ──────────────────────────────────
    Integration("rerank", "cohere", "Cohere Rerank", "rerank-v3 for result reordering.",
        "https://docs.cohere.com/docs/rerank", [_key(), _model("rerank-english-v3.0", required=True)], t.cohere),
    Integration("rerank", "voyage", "Voyage Rerank", "rerank-2 reranker.",
        "https://docs.voyageai.com", [_key(), _model("rerank-2", required=True)]),
    Integration("rerank", "jina", "Jina Reranker", "jina-reranker models.",
        "https://jina.ai/reranker", [_key(), _model("jina-reranker-v2-base-multilingual", required=True)]),

    # ───────────────────────────── Object store ──────────────────────────────
    Integration("object_store", "s3", "Amazon S3", "Store raw documents in S3.",
        "https://docs.aws.amazon.com/s3/", [
            Field("region", "Region", placeholder="us-east-1"),
            Field("bucket", "Bucket"),
            Field("access_key_id", "Access key ID", secret=True),
            Field("secret_access_key", "Secret access key", type="password", secret=True),
            _base_url("https://s3.amazonaws.com"),
        ]),
    Integration("object_store", "gcs", "Google Cloud Storage", "Store documents in GCS.",
        "https://cloud.google.com/storage/docs", [
            Field("bucket", "Bucket"),
            Field("service_account_json", "Service account JSON", type="password", secret=True),
        ]),
    Integration("object_store", "azure_blob", "Azure Blob Storage", "Store documents in Azure Blob.",
        "https://learn.microsoft.com/azure/storage/blobs/", [
            Field("account", "Storage account"),
            Field("container", "Container"),
            Field("connection_string", "Connection string", type="password", secret=True),
        ]),
    Integration("object_store", "minio", "MinIO / S3-compatible", "Self-hosted S3-compatible store.",
        "https://min.io/docs", [
            Field("endpoint", "Endpoint", placeholder="http://localhost:9000"),
            Field("bucket", "Bucket", default="metavita"),
            Field("access_key_id", "Access key", secret=True),
            Field("secret_access_key", "Secret key", type="password", secret=True),
        ]),

    # ───────────────────────────── Email ─────────────────────────────────────
    Integration("email", "smtp", "SMTP", "Send mail through any SMTP server.",
        "", [
            Field("host", "SMTP host", placeholder="smtp.gmail.com"),
            Field("port", "Port", type="number", default=587),
            Field("username", "Username"),
            Field("password", "Password", type="password", secret=True),
            Field("from_email", "From address", placeholder="you@example.com"),
            Field("use_tls", "Use STARTTLS", type="boolean", required=False, default=True),
        ]),
    Integration("email", "sendgrid", "SendGrid", "Twilio SendGrid transactional email.",
        "https://docs.sendgrid.com", [
            _key(ph="SG.…"),
            Field("from_email", "From address", placeholder="you@example.com"),
        ]),
    Integration("email", "mailgun", "Mailgun", "Mailgun email API.",
        "https://documentation.mailgun.com", [
            _key(),
            Field("domain", "Sending domain", placeholder="mg.example.com"),
            Field("region", "Region", type="select", options=["us", "eu"], default="us"),
            Field("from_email", "From address", placeholder="you@example.com"),
        ]),
    Integration("email", "postmark", "Postmark", "Postmark transactional email.",
        "https://postmarkapp.com/developer", [
            Field("server_token", "Server token", type="password", secret=True),
            Field("from_email", "From address", placeholder="you@example.com"),
        ]),
    Integration("email", "resend", "Resend", "Resend email API.",
        "https://resend.com/docs", [
            _key(ph="re_…"),
            Field("from_email", "From address", placeholder="you@example.com"),
        ]),
    Integration("email", "ses", "Amazon SES", "AWS Simple Email Service (SESv2).",
        "https://docs.aws.amazon.com/ses/", [
            Field("region", "AWS region", placeholder="us-east-1"),
            Field("access_key_id", "Access key ID", secret=True),
            Field("secret_access_key", "Secret access key", type="password", secret=True),
            Field("from_email", "From address", placeholder="you@example.com"),
        ]),
]


def build_registry() -> IntegrationRegistry:
    reg = IntegrationRegistry()
    for integ in INTEGRATIONS:
        reg.register(integ)
    return reg


default_integration_registry = build_registry()
