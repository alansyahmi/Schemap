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

export function determineBillingInfo(priceId?: string): { billingMode: string; planTier: string; expiresAt: string | null } {
  const now = new Date();
  let billingMode = "monthly";
  const planTier = "pro";

  if (priceId) {
    const p = priceId.toLowerCase();
    if (p.includes("lifetime")) billingMode = "lifetime";
    else if (p.includes("annual") || p.includes("year")) billingMode = "annual";
    else if (p.includes("quarter")) billingMode = "quarterly";
    else if (p.includes("semiannual") || p.includes("halfyear")) billingMode = "semiannual";
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

  const { billingMode, planTier, expiresAt } = determineBillingInfo(priceId);
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

    try {
      await sendLicenseEmail({
        apiKey: env.RESEND_API_KEY || "",
        fromEmail: env.FROM_EMAIL || "Schemap <onboarding@resend.dev>",
        toEmail: email,
        licenseKey: rawKey,
        billingMode: billingMode
      });
    } catch (e) {
      // Throw so Stripe retries the webhook. The existing license contains the
      // raw key, and the retry path below will resend that same key.
      console.log(`[EMAIL DISPATCH ERROR] Email sending failed: ${e}`);
      throw e;
    }
  } else if (existingLicense.raw_key_temp) {
    // Webhook retries must never generate a replacement key. Reuse the key
    // created for this checkout session when delivery previously failed.
    await sendLicenseEmail({
      apiKey: env.RESEND_API_KEY || "",
      fromEmail: env.FROM_EMAIL || "Schemap <onboarding@resend.dev>",
      toEmail: email,
      licenseKey: existingLicense.raw_key_temp,
      billingMode: existingLicense.billing_mode
    });
  }
}
