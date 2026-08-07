-- Evaluation schema migration
-- Version: 005
-- Description: Evaluation framework tables

-- Evaluation test cases
CREATE TABLE IF NOT EXISTS evaluation_cases (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    input_message TEXT NOT NULL,
    expected_output JSONB,
    expected_agent TEXT,
    expected_tools TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_evaluation_cases_category ON evaluation_cases(category);
CREATE INDEX idx_evaluation_cases_active ON evaluation_cases(is_active);

-- Evaluation runs
CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_name TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ,
    total_cases INTEGER,
    passed_cases INTEGER,
    failed_cases INTEGER,
    skipped_cases INTEGER,
    created_by TEXT,
    metadata JSONB
);

CREATE INDEX idx_evaluation_runs_started ON evaluation_runs(started_at DESC);

-- Evaluation results
CREATE TABLE IF NOT EXISTS evaluation_results (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES evaluation_runs(run_id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES evaluation_cases(case_id),
    passed BOOLEAN NOT NULL,
    actual_output JSONB,
    actual_agent TEXT,
    actual_tools TEXT[],
    duration_ms DOUBLE PRECISION,
    error_message TEXT,
    score DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_evaluation_results_run ON evaluation_results(run_id);
CREATE INDEX idx_evaluation_results_case ON evaluation_results(case_id);
CREATE INDEX idx_evaluation_results_passed ON evaluation_results(passed);

-- Record migration
INSERT INTO backend_schema_migrations (migration_id, description, checksum)
VALUES ('005_evaluation', 'Evaluation framework tables', 'v1')
ON CONFLICT (migration_id) DO NOTHING;
