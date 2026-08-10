import { Env, getLicenseByHash, getLicenseBySessionId, updateLicenseAudit } from "./db";
import { hashLicenseKey } from "./security";
import { verifyStripeSignature, processStripeEvent } from "./stripe";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, stripe-signature",
};

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;

    // Handle OPTIONS Preflight
    if (method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // 1. GET /health
    if (url.pathname === "/health" && method === "GET") {
      return jsonResponse({ status: "ok", service: "schemap-worker-license-api", version: "1.0.0" });
    }

    // 2. GET /v1/licenses/session-key?session_id=cs_...
    if (url.pathname === "/v1/licenses/session-key" && method === "GET") {
      const sessionId = url.searchParams.get("session_id");
      if (!sessionId) {
        return jsonResponse({ error: "Missing session_id parameter." }, 400);
      }
      const license = await getLicenseBySessionId(env.DB, sessionId);
      if (!license) {
        return jsonResponse({ status: "pending", message: "License is being generated..." }, 200);
      }
      return jsonResponse({
        status: "ready",
        license_key: license.raw_key_temp || `${license.key_prefix}...`,
        plan: license.billing_mode,
        expires_at: license.expires_at || null
      }, 200);
    }

    // 3. POST /webhooks/stripe
    if (url.pathname === "/webhooks/stripe" && method === "POST") {
      try {
        const rawBody = await request.text();
        const sigHeader = request.headers.get("stripe-signature");
        const secret = env.STRIPE_WEBHOOK_SECRET || "whsec_mock";

        const isValidSig = await verifyStripeSignature(rawBody, sigHeader, secret);
        if (!isValidSig) {
          return jsonResponse({ error: "Invalid Stripe signature" }, 400);
        }

        const event = JSON.parse(rawBody);
        const result = await processStripeEvent(event, env);
        return jsonResponse(result, 200);
      } catch (err: any) {
        return jsonResponse({ error: err.message || "Webhook processing error" }, 500);
      }
    }

    // 4. POST /v1/licenses/verify & POST /v1/licenses/activate
    if ((url.pathname === "/v1/licenses/verify" || url.pathname === "/v1/licenses/activate") && method === "POST") {
      try {
        const body: any = await request.json();
        const rawKey = body.license_key ? body.license_key.trim() : "";

        if (!rawKey) {
          return jsonResponse({ valid: false, activated: false, error: "Invalid license key format." }, 400);
        }

        const pepper = env.SERVER_PEPPER || "schemap_prod_pepper_v1_secret";
        const keyHash = await hashLicenseKey(rawKey, pepper);
        const license = await getLicenseByHash(env.DB, keyHash);

        if (!license) {
          return jsonResponse({ valid: false, activated: false, error: "Invalid or expired license key." }, 200);
        }

        const now = new Date();

        // Status evaluations
        if (license.status === "revoked" || license.status === "expired") {
          return jsonResponse({ valid: false, activated: false, error: "License revoked or expired." }, 200);
        }

        if (license.status === "past_due") {
          const updatedAt = new Date(license.updated_at || license.created_at);
          const graceUntil = new Date(updatedAt.getTime() + 7 * 86400 * 1000);
          if (now > graceUntil) {
            return jsonResponse({ valid: false, activated: false, error: "License suspended due to payment failure." }, 200);
          }
        }

        if (license.expires_at) {
          const expDate = new Date(license.expires_at);
          if (now > expDate) {
            await env.DB.prepare("UPDATE licenses SET status = 'expired' WHERE id = ?").bind(license.id).run();
            return jsonResponse({ valid: false, activated: false, error: "License subscription period has expired." }, 200);
          }
        }

        // Audit log
        ctx.waitUntil(updateLicenseAudit(env.DB, license.id, body.instance_name));

        return jsonResponse({
          valid: true,
          activated: true,
          tier: license.plan_tier,
          plan: license.billing_mode,
          expires_at: license.expires_at || null
        }, 200);

      } catch (err: any) {
        return jsonResponse({ valid: false, activated: false, error: err.message || "Verification request error" }, 500);
      }
    }

    // 5. POST /v1/licenses/deactivate
    if (url.pathname === "/v1/licenses/deactivate" && method === "POST") {
      return jsonResponse({ valid: true, deactivated: true });
    }

    return jsonResponse({ error: "Not found" }, 404);
  }
};

function jsonResponse(data: any, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...CORS_HEADERS
    }
  });
}
