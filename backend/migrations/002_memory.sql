-- Memory schema migration
-- Version: 002
-- Description: Customer memory and conversation summarization tables

-- Customer long-term memory
CREATE TABLE IF NOT EXISTS customer_memories (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id TEXT NOT NULL REFERENCES customer_profiles(customer_id),
    memory_type TEXT NOT NULL,
    memory_key TEXT,
    content TEXT,
    structured_value JSONB,
    source_conversation_id UUID REFERENCES conversations(conversation_id),
    source_message_id UUID REFERENCES messages(message_id),
    confidence DOUBLE PRECISION,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ,
    metadata JSONB
);

CREATE INDEX idx_customer_memories_customer ON customer_memories(customer_id);
CREATE INDEX idx_customer_memories_type ON customer_memories(memory_type);
CREATE INDEX idx_customer_memories_status ON customer_memories(status);
CREATE INDEX idx_customer_memories_created ON customer_memories(created_at DESC);
CREATE INDEX idx_customer_memories_expires ON customer_memories(expires_at) WHERE expires_at IS NOT NULL;

-- Conversation summaries
CREATE TABLE IF NOT EXISTS conversation_summaries (
    conversation_id UUID PRIMARY KEY REFERENCES conversations(conversation_id),
    customer_id TEXT NOT NULL REFERENCES customer_profiles(customer_id),
    summary TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_conversation_summaries_customer ON conversation_summaries(customer_id);

-- Record migration
INSERT INTO backend_schema_migrations (migration_id, description, checksum)
VALUES ('002_memory', 'Customer memory and summarization tables', 'v1')
ON CONFLICT (migration_id) DO NOTHING;
