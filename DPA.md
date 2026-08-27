# Schemap Data Processing Addendum (DPA) Template

**Effective Date:** January 1, 2026  
**Last Updated:** August 27, 2026  

This Data Processing Addendum ("DPA") supplements the Schemap Terms of Service entered into between Schemap AI and Customer.

---

## 1. Scope and Local Execution Guarantee

### Zero Production Customer Data Ingestion
1. **Local & Ephemeral Processing:** Schemap software operates strictly as a client-side compilation utility running locally within Customer's developer workstations or Customer's isolated CI/CD pipelines (e.g. GitHub Actions, GitLab CI).
2. **Metadata-Only Interaction:** Schemap queries only structural database system tables (`information_schema`, `pg_catalog`, `sqlite_master`) to extract column names, data types, and foreign key relations.
3. **No Row Data Transfer:** Schemap does not transmit, ingest, store, or process any application table rows, Customer PII, or confidential transactional records through Schemap cloud infrastructure.

---

## 2. Technical & Organizational Security Measures
* **PII Redaction Capabilities:** Schemap provides native `--sanitize` flags and keyword masking to prevent sensitive database column names from appearing in AI agent context instructions.
* **Encrypted Verification:** All license authentication requests utilize TLS 1.3 encryption.
* **Device Hash Non-Reversibility:** Device identifiers are salted and SHA-256 hashed prior to transmission.

---

## 3. Sub-Processors
Schemap engages the following sub-processors solely for billing and licensing transport:
* **Stripe, Inc.** (United States): Payment processing and subscription invoicing.
* **Cloudflare, Inc.** (Global Edge): Serverless license verification gateway.
* **Resend, Inc.** (United States): Transactional license key delivery.

---

## 4. Inquiries & Custom Execution
For enterprise DPA execution or procurement inquiries: **compliance@schemap.dev**
