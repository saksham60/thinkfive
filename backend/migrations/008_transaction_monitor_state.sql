CREATE TABLE IF NOT EXISTS transaction_monitor_state (
    customer_id TEXT PRIMARY KEY,
    baseline_established_at TIMESTAMPTZ NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

DO $$
BEGIN
    IF to_regclass('public.banking_transactions') IS NOT NULL THEN
        INSERT INTO transaction_processing_state (customer_id, transaction_id, metadata)
        SELECT bt.customer_id, bt.transaction_id, '{"reason":"existing_history_baseline"}'::jsonb
        FROM banking_transactions bt
        WHERE NOT EXISTS (
            SELECT 1
            FROM transaction_monitor_state monitor
            WHERE monitor.customer_id = bt.customer_id
        )
        ON CONFLICT (customer_id, transaction_id) DO NOTHING;

        INSERT INTO transaction_monitor_state (customer_id, baseline_established_at, metadata)
        SELECT DISTINCT customer_id, NOW(), '{"source":"migration_existing_history"}'::jsonb
        FROM banking_transactions
        ON CONFLICT (customer_id) DO NOTHING;
    END IF;
END $$;
