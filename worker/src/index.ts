import { Env, getLicenseByHash, getLicenseBySessionId, updateLicenseAudit, registerDeviceActivation, removeDeviceActivation } from "./db";
import { hashLicenseKey, hashDeviceFingerprint } from "./security";
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

    // 1b. GET /v1/stats/founders
    if (url.pathname === "/v1/stats/founders" && method === "GET") {
      try {
        const row = await env.DB.prepare(
          "SELECT COUNT(*) as claimed FROM licenses WHERE billing_mode = 'lifetime' AND status != 'revoked'"
        ).first<{ claimed: number }>();
        const claimed = Math.min(200, row?.claimed || 0);
        return jsonResponse({ total_cap: 200, claimed, remaining: Math.max(0, 200 - claimed) }, 200);
      } catch (err: any) {
        return jsonResponse({ total_cap: 200, claimed: 0, remaining: 200 }, 200);
      }
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
        const secret = env.STRIPE_WEBHOOK_SECRET || env.STRIPE_WEBHOOK_KEY || "whsec_mock";

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

        // Device Fingerprint & Seat Limit Registration
        const deviceId = body.device_id || body.instance_name || "default_device";
        const deviceFingerprint = await hashDeviceFingerprint(deviceId);
        const maxSeats = 3; // Pro & Founder Lifetime = 3 seats

        const activation = await registerDeviceActivation(
          env.DB,
          license.id,
          deviceFingerprint,
          body.instance_name,
          maxSeats
        );

        if (!activation.success) {
          return jsonResponse({
            valid: false,
            activated: false,
            error: activation.error || "Seat limit reached."
          }, 200);
        }

        // Audit log
        ctx.waitUntil(updateLicenseAudit(env.DB, license.id, body.instance_name));

        return jsonResponse({
          valid: true,
          activated: true,
          tier: license.plan_tier,
          plan: license.billing_mode,
          seats_used: activation.seatsUsed,
          max_seats: activation.maxSeats,
          expires_at: license.expires_at || null
        }, 200);

      } catch (err: any) {
        return jsonResponse({ valid: false, activated: false, error: err.message || "Verification request error" }, 500);
      }
    }

    // 5. POST /v1/licenses/deactivate
    if (url.pathname === "/v1/licenses/deactivate" && method === "POST") {
      try {
        const body: any = await request.json();
        const rawKey = body.license_key ? body.license_key.trim() : "";
        const deviceId = body.device_id || body.instance_name || "";

        if (rawKey && deviceId) {
          const pepper = env.SERVER_PEPPER || "schemap_prod_pepper_v1_secret";
          const keyHash = await hashLicenseKey(rawKey, pepper);
          const license = await getLicenseByHash(env.DB, keyHash);
          if (license) {
            const deviceFingerprint = await hashDeviceFingerprint(deviceId);
            await removeDeviceActivation(env.DB, license.id, deviceFingerprint);
          }
        }
        return jsonResponse({ valid: true, deactivated: true });
      } catch (err: any) {
        return jsonResponse({ valid: true, deactivated: true });
      }
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
