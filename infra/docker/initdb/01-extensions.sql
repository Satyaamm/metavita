-- Enable pgvector for embedding storage / similarity search.
CREATE EXTENSION IF NOT EXISTS vector;
-- pg_trgm supports hybrid (lexical) search alongside vector search.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
