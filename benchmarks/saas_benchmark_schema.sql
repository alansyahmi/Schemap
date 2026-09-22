-- Realistic Multi-Tenant B2B SaaS Schema with Traps
-- Dialect: PostgreSQL / SQLite compatible DDL

CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    tier TEXT NOT NULL DEFAULT 'standard',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    status TEXT NOT NULL DEFAULT 'active',
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    price_cents INTEGER NOT NULL,
    billing_interval TEXT NOT NULL DEFAULT 'monthly',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    plan_id INTEGER NOT NULL REFERENCES plans(id),
    status TEXT NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    invoice_number TEXT NOT NULL UNIQUE,
    amount_cents INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'paid',
    due_date TIMESTAMP NOT NULL,
    paid_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_amount_cents INTEGER NOT NULL,
    total_amount_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    provider_payment_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'succeeded',
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    event_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- SEED DATA

-- Organizations (Tenants)
INSERT INTO organizations (id, name, slug, tier) VALUES
(1, 'Acme Corp', 'acme-corp', 'enterprise'),
(2, 'Beta Inc', 'beta-inc', 'pro'),
(3, 'Stripe Killer', 'stripe-killer', 'starter');

-- Plans
INSERT INTO plans (id, name, code, price_cents, billing_interval) VALUES
(1, 'Starter Plan', 'starter', 4900, 'monthly'),
(2, 'Pro Plan', 'pro', 19900, 'monthly'),
(3, 'Enterprise Plan', 'enterprise', 99900, 'monthly');

-- Users
-- Note: Org 1 has 3 active users and 1 soft-deleted user
INSERT INTO users (id, org_id, email, full_name, role, status, deleted_at) VALUES
(1, 1, 'alice@acme.com', 'Alice Smith', 'owner', 'active', NULL),
(2, 1, 'bob@acme.com', 'Bob Jones', 'admin', 'active', NULL),
(3, 1, 'charlie@acme.com', 'Charlie Brown', 'member', 'active', NULL),
(4, 1, 'david@acme.com', 'David Miller', 'member', 'suspended', '2026-01-15 10:00:00'),

-- Org 2 has 2 active users and 1 soft-deleted user
(5, 2, 'eve@beta.com', 'Eve Wilson', 'owner', 'active', NULL),
(6, 2, 'frank@beta.com', 'Frank Castle', 'member', 'active', NULL),
(7, 2, 'grace@beta.com', 'Grace Hopper', 'member', 'inactive', '2026-02-01 12:00:00'),

-- Org 3 has 1 user
(8, 3, 'heidi@stripekiller.com', 'Heidi Klum', 'owner', 'active', NULL);

-- Subscriptions
INSERT INTO subscriptions (id, org_id, plan_id, status, current_period_start, current_period_end) VALUES
(1, 1, 3, 'active', '2026-01-01', '2026-02-01'),
(2, 2, 2, 'active', '2026-01-01', '2026-02-01'),
(3, 3, 1, 'canceled', '2025-12-01', '2026-01-01');

-- Invoices
INSERT INTO invoices (id, org_id, subscription_id, invoice_number, amount_cents, status, due_date, paid_at) VALUES
(1, 1, 1, 'INV-2026-001', 99900, 'paid', '2026-01-05', '2026-01-04'),
(2, 1, 1, 'INV-2026-002', 99900, 'paid', '2026-02-05', '2026-02-04'),
(3, 2, 2, 'INV-2026-003', 19900, 'paid', '2026-01-05', '2026-01-05'),
(4, 2, 2, 'INV-2026-004', 19900, 'open', '2026-02-05', NULL),
(5, 3, 3, 'INV-2026-005', 4900, 'void', '2026-01-05', NULL);

-- Invoice Items
INSERT INTO invoice_items (id, invoice_id, description, quantity, unit_amount_cents, total_amount_cents) VALUES
(1, 1, 'Enterprise Plan - Jan 2026', 1, 99900, 99900),
(2, 2, 'Enterprise Plan - Feb 2026', 1, 99900, 99900),
(3, 3, 'Pro Plan - Jan 2026', 1, 19900, 19900),
(4, 4, 'Pro Plan - Feb 2026', 1, 19900, 19900),
(5, 5, 'Starter Plan - Jan 2026', 1, 4900, 4900);

-- Payments
-- Note: Invoice 1 has 1 successful payment. Invoice 2 has 1 refunded/deleted payment and 1 successful payment.
INSERT INTO payments (id, invoice_id, provider_payment_id, amount_cents, status, deleted_at) VALUES
(1, 1, 'ch_acme_001', 99900, 'succeeded', NULL),
(2, 2, 'ch_acme_002_failed', 99900, 'failed', '2026-02-04 10:30:00'),
(3, 2, 'ch_acme_002_success', 99900, 'succeeded', NULL),
(4, 3, 'ch_beta_003', 19900, 'succeeded', NULL);

-- Usage Events
INSERT INTO usage_events (id, org_id, user_id, event_name, quantity) VALUES
(1, 1, 1, 'api_call', 500),
(2, 1, 2, 'api_call', 250),
(3, 1, 4, 'api_call', 100),
(4, 2, 5, 'export_pdf', 10),
(5, 2, 6, 'api_call', 50);
