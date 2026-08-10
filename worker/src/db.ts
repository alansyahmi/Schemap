export interface Env {
  DB: D1Database;
  ENVIRONMENT?: string;
  SERVER_PEPPER?: string;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  RESEND_API_KEY?: string;
  FROM_EMAIL?: string;
  IS_TEST_MODE?: string;
}

export interface CustomerRecord {
  id: number;
  stripe_customer_id: string;
  email: string;
  created_at: string;
}

export interface LicenseRecord {
  id: number;
  key_hash: string;
  key_prefix: string;
  customer_id: number;
  stripe_customer_id: string;
  stripe_subscription_id?: string;
  stripe_checkout_session_id: string;
  stripe_price_id?: string;
  plan_tier: string;
  billing_mode: string;
  status: string;
  expires_at?: string;
  raw_key_temp?: string;
  created_at: string;
  updated_at: string;
}

export async function upsertCustomer(db: D1Database, stripeCustomerId: string, email: string): Promise<number> {
  const existing = await db.prepare("SELECT id FROM customers WHERE stripe_customer_id = ?").bind(stripeCustomerId).first<CustomerRecord>();
  if (existing) {
    await db.prepare("UPDATE customers SET email = ?, updated_at = datetime('now') WHERE id = ?").bind(email, existing.id).run();
    return existing.id;
  }
  const result = await db.prepare("INSERT INTO customers (stripe_customer_id, email) VALUES (?, ?) RETURNING id").bind(stripeCustomerId, email).first<{ id: number }>();
  if (result) return result.id;
  
  const created = await db.prepare("SELECT id FROM customers WHERE stripe_customer_id = ?").bind(stripeCustomerId).first<CustomerRecord>();
  return created!.id;
}

export async function getLicenseByHash(db: D1Database, keyHash: string): Promise<LicenseRecord | null> {
  return await db.prepare("SELECT * FROM licenses WHERE key_hash = ?").bind(keyHash).first<LicenseRecord>();
}

export async function getLicenseBySessionId(db: D1Database, sessionId: string): Promise<LicenseRecord | null> {
  return await db.prepare("SELECT * FROM licenses WHERE stripe_checkout_session_id = ?").bind(sessionId).first<LicenseRecord>();
}

export async function createLicense(
  db: D1Database,
  data: {
    key_hash: string;
    key_prefix: string;
    customer_id: number;
    stripe_customer_id: string;
    stripe_subscription_id?: string;
    stripe_checkout_session_id: string;
    stripe_price_id?: string;
    stripe_payment_intent_id?: string;
    plan_tier: string;
    billing_mode: string;
    status: string;
    expires_at?: string;
    raw_key_temp?: string;
  }
): Promise<void> {
  await db.prepare(`
    INSERT INTO licenses (
      key_hash, key_prefix, customer_id, stripe_customer_id, stripe_subscription_id,
      stripe_checkout_session_id, stripe_price_id, stripe_payment_intent_id,
      plan_tier, billing_mode, status, expires_at, raw_key_temp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    data.key_hash,
    data.key_prefix,
    data.customer_id,
    data.stripe_customer_id,
    data.stripe_subscription_id || null,
    data.stripe_checkout_session_id,
    data.stripe_price_id || null,
    data.stripe_payment_intent_id || null,
    data.plan_tier,
    data.billing_mode,
    data.status,
    data.expires_at || null,
    data.raw_key_temp || null
  ).run();
}

export async function updateLicenseStatusBySubId(db: D1Database, subId: string, status: string, expiresAt?: string): Promise<void> {
  if (expiresAt) {
    await db.prepare("UPDATE licenses SET status = ?, expires_at = ?, updated_at = datetime('now') WHERE stripe_subscription_id = ?").bind(status, expiresAt, subId).run();
  } else {
    await db.prepare("UPDATE licenses SET status = ?, updated_at = datetime('now') WHERE stripe_subscription_id = ?").bind(status, subId).run();
  }
}

export async function revokeLicenseByCustomerOrPayment(db: D1Database, stripeCustomerId?: string, paymentIntentId?: string): Promise<void> {
  if (paymentIntentId) {
    await db.prepare("UPDATE licenses SET status = 'revoked', updated_at = datetime('now') WHERE stripe_payment_intent_id = ?").bind(paymentIntentId).run();
  } else if (stripeCustomerId) {
    await db.prepare("UPDATE licenses SET status = 'revoked', updated_at = datetime('now') WHERE stripe_customer_id = ?").bind(stripeCustomerId).run();
  }
}

export async function updateLicenseAudit(db: D1Database, licenseId: number, instanceName?: string): Promise<void> {
  await db.prepare("UPDATE licenses SET last_verified_at = datetime('now'), last_instance_name = ? WHERE id = ?").bind(instanceName || null, licenseId).run();
}
