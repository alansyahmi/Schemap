# Schemap Privacy Policy

**Effective Date:** January 1, 2026  
**Last Updated:** August 27, 2026  

Schemap AI ("Schemap", "we", "us", or "our") is committed to protecting your privacy and security. This Privacy Policy explains our data practices regarding the Schemap CLI, cloud services, and website (https://schemap.dev).

---

## 1. Core Principle: Zero Database Row Ingestion

**Schemap executes locally on your machines or within your CI/CD runners.**

* **No Row Data Ingestion:** Schemap connects to your database strictly to read table names, column definitions, data types, and foreign key constraints from system information catalogs (`information_schema`, `pg_catalog`, `sqlite_master`).
* **Zero Querying of Table Contents:** Schemap **never** executes `SELECT *` or retrieves any row-level application or customer data from your databases.
* **Local Compilation:** Markdown database contexts and AI agent instruction files are generated and stored exclusively on your local filesystem.

---

## 2. Information We Collect

### A. License Verification & Operational Telemetry
When you activate a Schemap Pro or Team license key:
* **License Key & Device Fingerprint:** SHA-256 hash of your device identifier (or CI runner ID) to enforce purchased seat concurrency limits.
* **Instance Name:** Hostname or CI job ID (e.g. `GitHub-Actions-Run-12345`) for device seat management.
* **Timestamps:** Last verification timestamp for offline license grace period enforcement.

### B. Account & Billing Information
Payments are processed directly via **Stripe**. We do not store raw credit card numbers or billing credentials on our servers. We receive:
* Customer email address
* Stripe Customer ID & Subscription ID
* Plan tier and seat quantity

---

## 3. How We Use Information
We use collected data solely to:
1. Verify software license validity and seat limits.
2. Deliver software updates and transactional receipts.
3. Prevent fraudulent reuse of commercial license keys.

---

## 4. Third-Party Service Providers
* **Stripe Inc.:** Payment processing and subscription management.
* **Cloudflare Workers & D1:** Zero-trust edge licensing API.
* **Resend:** Transactional email delivery for license keys.

---

## 5. Security & Data Retention
* License keys stored on user machines are protected with restricted file permissions (`0600` on Unix).
* License verification keys in transit are encrypted via TLS 1.3.
* Hashed device identifiers are permanently removed upon `schemap deactivate` or `schemap seats --revoke <device_id>`.

---

## 6. Contact Us
For any privacy or security questions:  
**Email:** privacy@schemap.dev  
**Website:** https://schemap.dev/security.html
