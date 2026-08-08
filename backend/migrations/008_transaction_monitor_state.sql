CREATE TABLE IF NOT EXISTS transaction_monitor_state (
    customer_id TEXT PRIMARY KEY,
    baseline_established_at TIMESTAMPTZ NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

DO $$
BEGIN
    IF to_regclass('public.banking_transactions') IS NOT NULL THEN
        INSERT INTO transaction_processing_state (customer_id, transaction_id, metadata)
        SELECT customer_id, transaction_id, '{"reason":"existing_history_baseline"}'::jsonb
        FROM banking_transactions
        ON CONFLICT (customer_id, transaction_id) DO NOTHING;

        INSERT INTO transaction_monitor_state (customer_id, baseline_established_at, metadata)
        SELECT DISTINCT customer_id, NOW(), '{"source":"migration_existing_history"}'::jsonb
        FROM banking_transactions
        ON CONFLICT (customer_id) DO NOTHING;
    END IF;
END $$;
