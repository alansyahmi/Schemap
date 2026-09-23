-- Seed Data for SaaS Trap Validation
-- Two Orgs: Org 1 (Acme Corp), Org 2 (Beta Inc)

-- Organizations
INSERT INTO organizations (id, name) VALUES (1, 'Acme Corp');
INSERT INTO organizations (id, name) VALUES (2, 'Beta Inc');

-- Users
-- Org 1 has 3 active users and 1 soft-deleted user ('zombie@acme.com')
INSERT INTO users (id, org_id, email, role, status, deleted_at) VALUES (1, 1, 'alice@acme.com', 'admin', 'active', NULL);
INSERT INTO users (id, org_id, email, role, status, deleted_at) VALUES (2, 1, 'bob@acme.com', 'member', 'active', NULL);
INSERT INTO users (id, org_id, email, role, status, deleted_at) VALUES (3, 1, 'charlie@acme.com', 'member', 'active', NULL);
INSERT INTO users (id, org_id, email, role, status, deleted_at) VALUES (4, 1, 'zombie@acme.com', 'member', 'inactive', '2026-01-15 10:00:00');

-- Org 2 users
INSERT INTO users (id, org_id, email, role, status, deleted_at) VALUES (5, 2, 'dana@beta.com', 'admin', 'active', NULL);
INSERT INTO users (id, org_id, email, role, status, deleted_at) VALUES (6, 2, 'edward@beta.com', 'member', 'inactive', '2026-02-01 12:00:00');

-- Plans
INSERT INTO plans (id, name, price_cents) VALUES (1, 'Starter Monthly', 4900);
INSERT INTO plans (id, name, price_cents) VALUES (2, 'Growth Enterprise', 199900);

-- Subscriptions
INSERT INTO subscriptions (id, org_id, plan_id, status) VALUES (1, 1, 2, 'active');
INSERT INTO subscriptions (id, org_id, plan_id, status) VALUES (2, 2, 1, 'active');

-- Invoices
-- Org 1 has 2 paid invoices: $1,999.00 and $1,999.00 = $3,998.00 total paid
INSERT INTO invoices (id, org_id, subscription_id, amount_cents, status) VALUES (1, 1, 1, 199900, 'paid');
INSERT INTO invoices (id, org_id, subscription_id, amount_cents, status) VALUES (2, 1, 1, 199900, 'paid');
INSERT INTO invoices (id, org_id, subscription_id, amount_cents, status) VALUES (3, 1, 1, 199900, 'void');
-- Org 2 has 1 paid invoice: $49.00
INSERT INTO invoices (id, org_id, subscription_id, amount_cents, status) VALUES (4, 2, 2, 4900, 'paid');

-- Usage Events
-- Org 1 active events: 10 + 25 = 35 total valid metric count; 1 soft-deleted event (100)
INSERT INTO usage_events (id, org_id, user_id, metric_count, deleted_at) VALUES (1, 1, 1, 10, NULL);
INSERT INTO usage_events (id, org_id, user_id, metric_count, deleted_at) VALUES (2, 1, 2, 25, NULL);
INSERT INTO usage_events (id, org_id, user_id, metric_count, deleted_at) VALUES (3, 1, 4, 100, '2026-01-16 08:00:00');
-- Org 2 events
INSERT INTO usage_events (id, org_id, user_id, metric_count, deleted_at) VALUES (4, 2, 5, 50, NULL);
