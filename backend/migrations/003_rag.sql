-- RAG schema migration
-- Version: 003
-- Description: Policy document storage and vector search

CREATE EXTENSION IF NOT EXISTS vector;

-- Policy documents
CREATE TABLE IF NOT EXISTS policy_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    document_type TEXT,
    version TEXT,
    jurisdiction TEXT,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_policy_documents_title ON policy_documents USING GIN(to_tsvector('english', title));
CREATE INDEX idx_policy_documents_type ON policy_documents(document_type);
CREATE INDEX idx_policy_documents_hash ON policy_documents(content_hash);

-- Policy chunks with embeddings
CREATE TABLE IF NOT EXISTS policy_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES policy_documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    page_number INTEGER,
    section_title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB,
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_policy_chunks_document ON policy_chunks(document_id);
CREATE INDEX idx_policy_chunks_content ON policy_chunks USING GIN(to_tsvector('english', content));
CREATE INDEX idx_policy_chunks_embedding ON policy_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Record migration
INSERT INTO backend_schema_migrations (migration_id, description, checksum)
VALUES ('003_rag', 'RAG policy document and vector tables', 'v1')
ON CONFLICT (migration_id) DO NOTHING;
