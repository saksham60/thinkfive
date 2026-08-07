-- Core schema migration
-- Version: 001
-- Description: Core backend tables

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Schema version tracking
CREATE TABLE IF NOT EXISTS backend_schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    checksum TEXT,
    description TEXT
);

-- App users (backend authentication)
CREATE TABLE IF NOT EXISTS app_users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT,
    role TEXT NOT NULL DEFAULT 'CUSTOMER',
    customer_id TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_app_users_email ON app_users(email);
CREATE INDEX idx_app_users_customer_id ON app_users(customer_id);
CREATE INDEX idx_app_users_role ON app_users(role);

-- Customer profiles
CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id TEXT PRIMARY KEY,
    email TEXT,
    phone TEXT,
    first_name TEXT,
    last_name TEXT,
    preferred_language TEXT DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_customer_profiles_email ON customer_profiles(email);

-- Customer cards metadata
CREATE TABLE IF NOT EXISTS customer_cards (
    card_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customer_profiles(customer_id),
    card_last_four TEXT,
    card_brand TEXT,
    card_type TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_customer_cards_customer ON customer_cards(customer_id);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id TEXT NOT NULL REFERENCES customer_profiles(customer_id),
    title TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_conversations_status ON conversations(status);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB,
    tool_calls JSONB,
    tool_call_id TEXT
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_role ON messages(role);

-- Agent runs
CREATE TABLE IF NOT EXISTS agent_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    customer_id TEXT NOT NULL REFERENCES customer_profiles(customer_id),
    thread_id TEXT NOT NULL,
    status TEXT DEFAULT 'QUEUED',
    model TEXT,
    provider TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms DOUBLE PRECISION,
    token_usage JSONB,
    cost_usd DOUBLE PRECISION,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_agent_runs_conversation ON agent_runs(conversation_id);
CREATE INDEX idx_agent_runs_customer ON agent_runs(customer_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
CREATE INDEX idx_agent_runs_created ON agent_runs(created_at DESC);

-- Agent events
CREATE TABLE IF NOT EXISTS agent_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_seq BIGSERIAL,
    run_id UUID NOT NULL REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    customer_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    agent_name TEXT,
    tool_name TEXT,
    status TEXT,
    duration_ms DOUBLE PRECISION,
    correlation_id TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_agent_events_run ON agent_events(run_id);
CREATE INDEX idx_agent_events_conversation ON agent_events(conversation_id);
CREATE INDEX idx_agent_events_customer ON agent_events(customer_id);
CREATE INDEX idx_agent_events_type ON agent_events(event_type);
CREATE INDEX idx_agent_events_seq ON agent_events(event_seq);
CREATE INDEX idx_agent_events_created ON agent_events(created_at DESC);

-- Transaction processing state
CREATE TABLE IF NOT EXISTS transaction_processing_state (
    customer_id TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    assessment_id TEXT,
    alert_id TEXT,
    metadata JSONB,
    PRIMARY KEY (customer_id, transaction_id)
);

CREATE INDEX idx_transaction_processing_customer ON transaction_processing_state(customer_id);
CREATE INDEX idx_transaction_processing_processed ON transaction_processing_state(processed_at DESC);

-- Workflow interrupts
CREATE TABLE IF NOT EXISTS workflow_interrupts (
    interrupt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES agent_runs(run_id),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    thread_id TEXT NOT NULL,
    customer_id TEXT,
    case_id TEXT,
    approval_id TEXT,
    interrupt_type TEXT NOT NULL,
    status TEXT DEFAULT 'WAITING',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by_user_id UUID REFERENCES app_users(user_id),
    resume_payload JSONB,
    metadata JSONB
);

CREATE INDEX idx_workflow_interrupts_run ON workflow_interrupts(run_id);
CREATE INDEX idx_workflow_interrupts_conversation ON workflow_interrupts(conversation_id);
CREATE INDEX idx_workflow_interrupts_approval ON workflow_interrupts(approval_id);
CREATE INDEX idx_workflow_interrupts_status ON workflow_interrupts(status);
CREATE INDEX idx_workflow_interrupts_created ON workflow_interrupts(created_at DESC);

-- Insert demo customer
INSERT INTO customer_profiles (customer_id, email, first_name, last_name)
VALUES ('demo_customer_001', 'demo@thinkfive.ai', 'Demo', 'Customer')
ON CONFLICT (customer_id) DO NOTHING;

-- Insert demo user
INSERT INTO app_users (email, role, customer_id, hashed_password)
VALUES ('demo@thinkfive.ai', 'CUSTOMER', 'demo_customer_001', '$2b$12$ug0GbmCtlhFDk9JEGOWD0ujC3BogvQhOsPcxyTnXRLSN/U8kxypoG')
ON CONFLICT (email) DO NOTHING;

-- Insert demo analyst
INSERT INTO app_users (email, role, hashed_password)
VALUES ('analyst@thinkfive.ai', 'ANALYST', '$2b$12$NafccG65kpW7LzK9Y/F08uqYhrdsHYuHkru6KMDGD5LUdFN9ku6bW')
ON CONFLICT (email) DO NOTHING;

-- Record migration
INSERT INTO backend_schema_migrations (migration_id, description, checksum)
VALUES ('001_core', 'Core backend tables', 'v1')
ON CONFLICT (migration_id) DO NOTHING;
