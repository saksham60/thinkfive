CREATE TABLE IF NOT EXISTS banking_connections (
    customer_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL DEFAULT 'SYNTHETIC',
    status TEXT NOT NULL DEFAULT 'CONNECTED',
    external_item_id TEXT,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS banking_accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    name TEXT NOT NULL,
    official_name TEXT,
    account_type TEXT NOT NULL,
    account_subtype TEXT,
    mask TEXT,
    current_balance NUMERIC(18,2),
    available_balance NUMERIC(18,2),
    iso_currency_code TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    source TEXT NOT NULL DEFAULT 'SYNTHETIC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS banking_transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_id TEXT NOT NULL REFERENCES banking_accounts(account_id) ON DELETE CASCADE,
    amount NUMERIC(18,2) NOT NULL,
    merchant_name TEXT,
    description TEXT NOT NULL,
    category TEXT,
    pending BOOLEAN NOT NULL DEFAULT FALSE,
    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
    authorized_at TIMESTAMPTZ,
    posted_at TIMESTAMPTZ,
    iso_currency_code TEXT NOT NULL DEFAULT 'USD',
    source TEXT NOT NULL DEFAULT 'SYNTHETIC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_banking_accounts_customer_status
    ON banking_accounts(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_banking_transactions_customer_date
    ON banking_transactions(customer_id, transaction_date DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_banking_transactions_customer_account
    ON banking_transactions(customer_id, account_id);
CREATE INDEX IF NOT EXISTS idx_banking_transactions_customer_merchant
    ON banking_transactions(customer_id, merchant_name);

ALTER TABLE banking_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE banking_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE banking_transactions ENABLE ROW LEVEL SECURITY;

INSERT INTO banking_connections (customer_id, provider, status, metadata)
VALUES ('demo_customer_001', 'SYNTHETIC', 'CONNECTED', '{"seed":"thinkfive_demo"}'::jsonb)
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO banking_accounts (
    account_id, customer_id, name, official_name, account_type, account_subtype,
    mask, current_balance, available_balance, iso_currency_code, status, source, metadata
)
VALUES
    ('acct_demo_checking', 'demo_customer_001', 'Checking', 'Demo Checking Account', 'depository', 'checking',
     '6620', 500.00, 500.00, 'USD', 'ACTIVE', 'SYNTHETIC', '{"seed":"thinkfive_demo"}'::jsonb),
    ('acct_demo_credit', 'demo_customer_001', 'Credit Card', 'Demo Credit Card', 'credit', 'credit card',
     '4666', 500.00, 500.00, 'USD', 'ACTIVE', 'SYNTHETIC', '{"seed":"thinkfive_demo"}'::jsonb)
ON CONFLICT (account_id) DO NOTHING;

INSERT INTO banking_transactions (
    transaction_id, customer_id, account_id, amount, merchant_name, description,
    category, pending, transaction_date, authorized_at, posted_at,
    iso_currency_code, source, metadata
)
SELECT
    'txn_demo_history_' || LPAD(n::text, 3, '0'),
    'demo_customer_001',
    CASE WHEN n % 4 = 0 THEN 'acct_demo_credit' ELSE 'acct_demo_checking' END,
    ROUND((8.50 + ((n * 17) % 103) + ((n % 4) * 0.19))::numeric, 2),
    (ARRAY['Neighborhood Market', 'City Cafe', 'Metro Transit', 'Corner Pharmacy', 'Fuel Station', 'Streaming Service'])[1 + ((n - 1) % 6)],
    (ARRAY['Neighborhood Market Purchase', 'City Cafe Purchase', 'Metro Transit Fare', 'Corner Pharmacy Purchase', 'Fuel Station Purchase', 'Streaming Service Subscription'])[1 + ((n - 1) % 6)],
    (ARRAY['Groceries', 'Food and Drink', 'Transportation', 'Healthcare', 'Fuel', 'Entertainment'])[1 + ((n - 1) % 6)],
    FALSE,
    CURRENT_DATE - (1 + ((n - 1) % 35)),
    (CURRENT_DATE - (1 + ((n - 1) % 35)))::timestamptz + INTERVAL '12 hours',
    (CURRENT_DATE - (1 + ((n - 1) % 35)))::timestamptz + INTERVAL '14 hours',
    'USD',
    'SYNTHETIC',
    jsonb_build_object(
        'seed', 'thinkfive_normal_history_v1',
        'payment_channel', CASE WHEN n % 3 = 0 THEN 'online' ELSE 'in store' END,
        'location', jsonb_build_object('city', 'Austin', 'region', 'TX', 'country', 'US')
    )
FROM generate_series(1, 40) AS n
WHERE NOT EXISTS (
    SELECT 1 FROM banking_transactions WHERE customer_id = 'demo_customer_001'
)
ON CONFLICT (transaction_id) DO NOTHING;
