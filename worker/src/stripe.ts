import { Env, upsertCustomer, getLicenseBySessionId, createLicense, updateLicenseStatusBySubId, revokeLicenseByCustomerOrPayment } from "./db";
import { generateLicenseKey, hashLicenseKey, getKeyPrefix } from "./security";
import { sendLicenseEmail } from "./mailer";

export async function verifyStripeSignature(rawBody: string, sigHeader: string | null, secret: string): Promise<boolean> {
  if (!secret || secret === "whsec_mock") return true;
  if (!sigHeader) return false;

  const parts = sigHeader.split(",");
  let timestamp = "";
  let v1Sig = "";

  for (const part of parts) {
    const [key, val] = part.trim().split("=");
    if (key === "t") timestamp = val;
    if (key === "v1") v1Sig = val;
  }

  if (!timestamp || !v1Sig) return false;

  const signedPayload = `${timestamp}.${rawBody}`;
  const encoder = new TextEncoder();

  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  const sigBuffer = await crypto.subtle.sign("HMAC", key, encoder.encode(signedPayload));
  const expectedSig = Array.from(new Uint8Array(sigBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  return expectedSig === v1Sig;
}

export async function fetchStripeObject(path: string, apiKey: string): Promise<any | null> {
  if (!path || !apiKey || apiKey === "whsec_mock") return null;
  try {
    const res = await fetch(`https://api.stripe.com/v1/${path}`, {
      headers: { Authorization: `Bearer ${apiKey}` }
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    // ignore network errors
  }
  return null;
}

/**
 * SCHEMAP LICENSING RESOLUTION PIPELINE (3-TIER ARCHITECTURE)
 * -----------------------------------------------------------------------------
 * When Stripe fires a checkout.session.completed webhook, determineBillingInfo()
 * resolves the plan type (monthly, quarterly, semiannual, annual, lifetime)
 * using a 3-tier fallback strategy so pricing or URL updates never break licensing:
 *
 * Tier 1: Explicit Metadata & Checkout Mode
 * - Checks session.metadata.plan or plinkObj.metadata.plan ('monthly', 'quarterly', 'semiannual', 'annual', 'lifetime')
 * - Checks session.mode === 'payment' -> Founder Lifetime Pro (expires_at = null)
 *
 * Tier 2: Stripe API Subscription Object Inspection
 * - Calls /v1/subscriptions/{sub_id} via STRIPE_SECRET_KEY
 * - Inspects recurring.interval & recurring.interval_count:
 *     - 'year' or count >= 12  -> Annual Pro
 *     - 'month' & count >= 5  -> 6-Month (Semiannual) Pro
 *     - 'month' & count >= 3  -> Quarterly Pro
 *     - 'month' & count == 1  -> Monthly Pro
 *
 * Tier 3: Price Amount Range Fallback (in Cents)
 * - >= 7700 cents ($77+)  -> Lifetime Pro
 * - >= 5500 cents ($55+)  -> Annual Pro
 * - >= 3200 cents ($32+)  -> 6-Month Pro
 * - >= 1600 cents ($16+)  -> Quarterly Pro (Matches $21.99 + tax/discounts)
 * - < 1600 cents          -> Monthly Pro
 * -----------------------------------------------------------------------------
 */
export function determineBillingInfo(session: any, extraData?: { lineItems?: any; subObj?: any; plinkObj?: any }): { billingMode: string; planTier: string; expiresAt: string | null } {
  const now = new Date();
  let billingMode = "monthly";
  const planTier = "pro";

  const mode = (session.mode || "").toLowerCase();
  const metaPlan = (
    session.metadata?.plan || 
    session.metadata?.billing_mode || 
    extraData?.plinkObj?.metadata?.plan ||
    extraData?.plinkObj?.metadata?.billing_mode ||
    ""
  ).toLowerCase();
  
  const amountCents = Number(session.amount_total || session.amount_subtotal || 0);

  // 1. One-time payment in Stripe is ALWAYS Lifetime
  if (mode === "payment" || metaPlan.includes("lifetime") || metaPlan.includes("founder")) {
    billingMode = "lifetime";
  } else if (metaPlan.includes("annual") || metaPlan.includes("year")) {
    billingMode = "annual";
  } else if (metaPlan.includes("semiannual") || metaPlan.includes("halfyear") || metaPlan.includes("6month")) {
    billingMode = "semiannual";
  } else if (metaPlan.includes("quarter") || metaPlan.includes("3month")) {
    billingMode = "quarterly";
  } else {
    // 2. Check Subscription object interval from Stripe API
    const subItem = extraData?.subObj?.items?.data?.[0];
    const recurring = subItem?.plan || subItem?.price?.recurring;
    
    if (recurring) {
      const interval = recurring.interval;
      const count = recurring.interval_count || 1;

      if (interval === "year" || count >= 12) {
        billingMode = "annual";
      } else if (interval === "month" && count >= 5) {
        billingMode = "semiannual";
      } else if (interval === "month" && count >= 3) {
        billingMode = "quarterly";
      } else {
        billingMode = "monthly";
      }
    } else if (amountCents >= 7700) {
      // 3. Amount Range Fallback (handles taxes/discounts seamlessly)
      billingMode = "lifetime";
    } else if (amountCents >= 5500) {
      billingMode = "annual";
    } else if (amountCents >= 3200) {
      billingMode = "semiannual";
    } else if (amountCents >= 1600) {
      billingMode = "quarterly"; // Matches 2499 ($21.99 + tax)!
    } else {
      billingMode = "monthly";
    }
  }

  let expiresAt: string | null = null;
  if (billingMode === "lifetime") {
    expiresAt = null;
  } else if (billingMode === "annual") {
    now.setDate(now.getDate() + 368);
    expiresAt = now.toISOString();
  } else if (billingMode === "semiannual") {
    now.setDate(now.getDate() + 186);
    expiresAt = now.toISOString();
  } else if (billingMode === "quarterly") {
    now.setDate(now.getDate() + 95);
    expiresAt = now.toISOString();
  } else {
    now.setDate(now.getDate() + 32);
    expiresAt = now.toISOString();
  }

  return { billingMode, planTier, expiresAt };
}

export async function processStripeEvent(event: any, env: Env): Promise<{ status: string; event_id: string }> {
  const eventId = event.id;
  const eventType = event.type;

  if (!eventId || !eventType) {
    throw new Error("Invalid Stripe event structure.");
  }

  // Check idempotency in D1
  const existingEvent = await env.DB.prepare("SELECT status FROM stripe_events WHERE event_id = ?").bind(eventId).first<{ status: string }>();
  if (existingEvent && existingEvent.status === "completed") {
    return { status: "already_processed", event_id: eventId };
  }

  await env.DB.prepare("INSERT OR REPLACE INTO stripe_events (event_id, event_type, status, attempts) VALUES (?, ?, 'processing', 1)").bind(eventId, eventType).run();

  try {
    const dataObj = event.data?.object || {};

    if (eventType === "checkout.session.completed") {
      const debugPayload = JSON.stringify({
        mode: dataObj.mode,
        amount_total: dataObj.amount_total,
        payment_link: dataObj.payment_link,
        metadata: dataObj.metadata,
        subscription: dataObj.subscription,
        price_id: dataObj.price_id,
        keys: Object.keys(dataObj)
      });
      await env.DB.prepare("UPDATE stripe_events SET last_error = ? WHERE event_id = ?").bind(debugPayload, eventId).run();
      await handleCheckoutCompleted(dataObj, env);
    } else if (eventType === "customer.subscription.updated") {
      const subId = dataObj.id;
      const subStatus = dataObj.status;
      const periodEnd = dataObj.current_period_end;
      const expiresAt = periodEnd ? new Date(periodEnd * 1000 + 2 * 86400 * 1000).toISOString() : undefined;
      const statusMap: Record<string, string> = { active: "active", past_due: "past_due", unpaid: "past_due", canceled: "canceled" };
      if (subId) {
        await updateLicenseStatusBySubId(env.DB, subId, statusMap[subStatus] || "active", expiresAt);
      }
    } else if (eventType === "customer.subscription.deleted") {
      if (dataObj.id) {
        await updateLicenseStatusBySubId(env.DB, dataObj.id, "canceled");
      }
    } else if (eventType === "invoice.payment_failed") {
      if (dataObj.subscription) {
        await updateLicenseStatusBySubId(env.DB, dataObj.subscription, "past_due");
      }
    } else if (eventType === "charge.refunded" || eventType === "charge.dispute.created") {
      await revokeLicenseByCustomerOrPayment(env.DB, dataObj.customer, dataObj.payment_intent);
    }

    await env.DB.prepare("UPDATE stripe_events SET status = 'completed', processed_at = datetime('now') WHERE event_id = ?").bind(eventId).run();
    return { status: "success", event_id: eventId };
  } catch (err: any) {
    await env.DB.prepare("UPDATE stripe_events SET status = 'failed', last_error = ? WHERE event_id = ?").bind(err.message || String(err), eventId).run();
    throw err;
  }
}

export async function handleCheckoutCompleted(session: any, env: Env): Promise<void> {
  const sessionId = session.id;
  const stripeCustomerId = session.customer || session.customer_id || `cus_anon_${sessionId}`;
  const customerDetails = session.customer_details || {};
  const email = customerDetails.email || session.customer_email || "buyer@example.com";
  const subId = session.subscription;
  const paymentIntentId = session.payment_intent;
  const priceId = session.price_id || session.metadata?.price_id;

  const extraData: any = {};
  if (env.STRIPE_SECRET_KEY) {
    if (session.payment_link) {
      extraData.plinkObj = await fetchStripeObject(`payment_links/${session.payment_link}`, env.STRIPE_SECRET_KEY);
    }
    if (session.subscription) {
      extraData.subObj = await fetchStripeObject(`subscriptions/${session.subscription}`, env.STRIPE_SECRET_KEY);
    }
  }

  const { billingMode, planTier, expiresAt } = determineBillingInfo(session, extraData);
  const customerId = await upsertCustomer(env.DB, stripeCustomerId, email);

  const existingLicense = await getLicenseBySessionId(env.DB, sessionId);
  if (!existingLicense) {
    const isTestMode = (env.IS_TEST_MODE === "true") || (sessionId && sessionId.startsWith("cs_test_"));
    const rawKey = generateLicenseKey(isTestMode);
    const pepper = env.SERVER_PEPPER || "schemap_prod_pepper_v1_secret";
    const keyHash = await hashLicenseKey(rawKey, pepper);
    const keyPrefix = getKeyPrefix(rawKey);

    await createLicense(env.DB, {
      key_hash: keyHash,
      key_prefix: keyPrefix,
      customer_id: customerId,
      stripe_customer_id: stripeCustomerId,
      stripe_subscription_id: subId,
      stripe_checkout_session_id: sessionId,
      stripe_price_id: priceId,
      stripe_payment_intent_id: paymentIntentId,
      plan_tier: planTier,
      billing_mode: billingMode,
      status: "active",
      expires_at: expiresAt || undefined,
      raw_key_temp: rawKey
    });
  }
}
