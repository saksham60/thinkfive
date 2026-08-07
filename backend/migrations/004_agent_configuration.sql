-- Agent configuration migration
-- Version: 004
-- Description: Agent and prompt configuration tables

-- Prompt templates
CREATE TABLE IF NOT EXISTS prompt_templates (
    prompt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name TEXT NOT NULL,
    version TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_by TEXT,
    metadata JSONB,
    UNIQUE(agent_name, version)
);

CREATE INDEX idx_prompt_templates_agent ON prompt_templates(agent_name);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(agent_name, is_active) WHERE is_active = TRUE;

-- Agent configurations
CREATE TABLE IF NOT EXISTS agent_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name TEXT NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    provider TEXT,
    model TEXT,
    temperature DOUBLE PRECISION,
    max_iterations INTEGER,
    allowed_tools TEXT[],
    active_prompt_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_agent_configs_agent ON agent_configs(agent_name);
CREATE INDEX idx_agent_configs_enabled ON agent_configs(enabled);

-- Record migration
INSERT INTO backend_schema_migrations (migration_id, description, checksum)
VALUES ('004_agent_configuration', 'Agent and prompt configuration tables', 'v1')
ON CONFLICT (migration_id) DO NOTHING;
