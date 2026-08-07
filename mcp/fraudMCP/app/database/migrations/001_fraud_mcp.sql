begin;
create extension if not exists pgcrypto;

create table if not exists public.fraud_assessments (
    assessment_id uuid primary key,
    customer_id text not null,
    transaction_id text not null,
    risk_score double precision not null check (risk_score >= 0 and risk_score <= 1),
    severity text not null check (severity in ('LOW','MEDIUM','HIGH','CRITICAL')),
    created_at timestamptz not null,
    payload jsonb not null
);
create index if not exists fraud_assessments_customer_created_idx on public.fraud_assessments(customer_id, created_at desc);
create index if not exists fraud_assessments_transaction_idx on public.fraud_assessments(customer_id, transaction_id, created_at desc);

create table if not exists public.fraud_alerts (
    alert_id uuid primary key,
    assessment_id uuid not null references public.fraud_assessments(assessment_id),
    customer_id text not null,
    transaction_id text not null,
    risk_score double precision not null check (risk_score >= 0 and risk_score <= 1),
    severity text not null check (severity in ('LOW','MEDIUM','HIGH','CRITICAL')),
    priority text not null check (priority in ('LOW','MEDIUM','HIGH','URGENT')),
    status text not null check (status in ('OPEN','INVESTIGATING','ESCALATED','RESOLVED','FALSE_POSITIVE')),
    created_at timestamptz not null,
    updated_at timestamptz not null,
    payload jsonb not null,
    unique(customer_id, transaction_id)
);
create index if not exists fraud_alerts_customer_created_idx on public.fraud_alerts(customer_id, created_at desc);
create index if not exists fraud_alerts_status_idx on public.fraud_alerts(status);

create table if not exists public.customer_devices (
    customer_id text not null,
    device_id text not null,
    payload jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now(),
    primary key(customer_id, device_id)
);

create table if not exists public.blacklist_entities (
    entity_type text not null,
    normalized_value text not null,
    payload jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now(),
    primary key(entity_type, normalized_value)
);

alter table public.fraud_assessments enable row level security;
alter table public.fraud_alerts enable row level security;
alter table public.customer_devices enable row level security;
alter table public.blacklist_entities enable row level security;
revoke all on public.fraud_assessments, public.fraud_alerts, public.customer_devices, public.blacklist_entities from anon, authenticated;
commit;
notify pgrst, 'reload schema';
