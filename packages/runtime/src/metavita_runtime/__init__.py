"""MetaVita runtime engine (M0 slice: ingest + retrieve/answer)."""

from .answer import answer_question, stream_answer
from .chunking import chunk_text
from .executor import PipelineRunOutput, execute_pipeline
from .graph import (
    EMPTY_GRAPH,
    NODE_TYPES,
    NodeType,
    has_cycle,
    is_valid_graph,
    topological_order,
    validate_graph,
)
from .ingest import ingest_document
from .parsing import parse
from .types import Answer, Chunk, Citation, RetrievedChunk, VectorStore

__all__ = [
    "answer_question",
    "stream_answer",
    "chunk_text",
    "execute_pipeline",
    "PipelineRunOutput",
    "ingest_document",
    "parse",
    "Answer",
    "Chunk",
    "Citation",
    "RetrievedChunk",
    "VectorStore",
    "EMPTY_GRAPH",
    "NODE_TYPES",
    "NodeType",
    "has_cycle",
    "is_valid_graph",
    "topological_order",
    "validate_graph",
]
