-- Cloudflare D1 SQL Database Schema for Schemap License API

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_customer_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    key_prefix TEXT NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    stripe_customer_id TEXT NOT NULL,
    stripe_subscription_id TEXT UNIQUE,
    stripe_checkout_session_id TEXT UNIQUE NOT NULL,
    stripe_price_id TEXT,
    stripe_payment_intent_id TEXT,
    plan_tier TEXT DEFAULT 'pro',
    billing_mode TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    expires_at TEXT,
    raw_key_temp TEXT,
    last_verified_at TEXT,
    last_instance_name TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stripe_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing',
    attempts INTEGER NOT NULL DEFAULT 1,
    last_error TEXT,
    processed_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_licenses_key_hash ON licenses(key_hash);
CREATE INDEX IF NOT EXISTS idx_licenses_sub_id ON licenses(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_licenses_session_id ON licenses(stripe_checkout_session_id);
