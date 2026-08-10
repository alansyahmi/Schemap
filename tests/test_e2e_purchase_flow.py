import pytest
import os
import json
from pathlib import Path
from click.testing import CliRunner
from fastapi.testclient import TestClient

from server.app import app
from server.database import Base, engine, SessionLocal, Customer, License, StripeEvent
from server.security import hash_license_key
from schemap.cli import cli
from schemap.license import load_credentials, clear_credentials, resolve_license_key

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_env_and_db():
    clear_credentials()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    if Path("schemap_database_context.md").exists():
        try:
            Path("schemap_database_context.md").unlink()
        except Exception:
            pass
    yield
    clear_credentials()
    Base.metadata.drop_all(bind=engine)
    if Path("schemap_database_context.md").exists():
        try:
            Path("schemap_database_context.md").unlink()
        except Exception:
            pass

def test_full_end_to_end_purchase_and_cli_activation(mocker, tmp_path):
    """
    Tests the complete purchase flow end-to-end:
    1. Customer pays via Stripe (simulated checkout.session.completed webhook).
    2. License server receives webhook, creates Customer & License, sends delivery email.
    3. User runs `schemap activate <key>` pointing to server.
    4. CLI verifies key against server /v1/licenses/verify and saves global credentials.
    5. `schemap status` confirms Pro tier.
    6. `schemap context` compiles schema with active Pro key.
    7. Charge refund revokes key.
    """
    # Capture email dispatch
    captured_emails = []
    def mock_send_email(recipient_email, license_key, billing_mode):
        captured_emails.append({
            "to": recipient_email,
            "key": license_key,
            "billing_mode": billing_mode
        })
        return {"status": "mock_sent"}

    mocker.patch("server.stripe_handler.send_license_email", side_effect=mock_send_email)

    # -------------------------------------------------------------------------
    # STEP 1 & 2: Stripe Checkout Payment & Webhook Delivery
    # -------------------------------------------------------------------------
    buyer_email = "dev_founder@example.com"
    checkout_session_event = {
        "id": "evt_e2e_purchase_999",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_e2e_session",
                "customer": "cus_e2e_founder_001",
                "customer_details": {"email": buyer_email},
                "price_id": "price_annual"
            }
        }
    }

    # Send webhook to FastAPI license server
    webhook_response = client.post("/webhooks/stripe", json=checkout_session_event)
    assert webhook_response.status_code == 200
    assert webhook_response.json()["status"] == "success"

    # Verify email was dispatched to buyer with their generated key
    assert len(captured_emails) == 1
    issued_key = captured_emails[0]["key"]
    assert issued_key.startswith("sch_test_") or issued_key.startswith("sch_live_")
    assert captured_emails[0]["to"] == buyer_email
    assert captured_emails[0]["billing_mode"] == "annual"

    # Verify Database state
    db = SessionLocal()
    customer_db = db.query(Customer).filter(Customer.stripe_customer_id == "cus_e2e_founder_001").first()
    assert customer_db is not None
    assert customer_db.email == buyer_email

    expected_hash = hash_license_key(issued_key)
    license_db = db.query(License).filter(License.key_hash == expected_hash).first()
    assert license_db is not None
    assert license_db.billing_mode == "annual"
    assert license_db.status == "active"
    db.close()

    # -------------------------------------------------------------------------
    # STEP 3 & 4: CLI Activation (`schemap activate <issued_key>`)
    # -------------------------------------------------------------------------
    # Mock verify_license_online in CLI to route to FastAPI TestClient
    def mock_cli_verify_online(license_key, endpoint):
        res = client.post("/v1/licenses/verify", json={
            "license_key": license_key,
            "instance_name": "developer-laptop"
        })
        return res.json()

    mocker.patch("schemap.cli.verify_license_online", side_effect=mock_cli_verify_online)
    mocker.patch("schemap.license.verify_license_online", side_effect=mock_cli_verify_online)

    runner = CliRunner()
    
    # User runs: schemap activate sch_test_...
    activate_res = runner.invoke(cli, ["activate", issued_key])
    assert activate_res.exit_code == 0
    assert "License activated successfully" in activate_res.output

    # Check global credentials file was written
    creds = load_credentials()
    assert creds is not None
    assert creds["license_key"] == issued_key

    # -------------------------------------------------------------------------
    # STEP 5: Verify CLI Status (`schemap status`)
    # -------------------------------------------------------------------------
    status_res = runner.invoke(cli, ["status"])
    assert status_res.exit_code == 0
    assert "Tier:             Pro" in status_res.output
    assert "Key Source:       global_credentials" in status_res.output

    # -------------------------------------------------------------------------
    # STEP 6: Execute CLI Context Compilation (`schemap context`)
    # -------------------------------------------------------------------------
    # Setup test schemap.yaml and test sqlite db
    config_path = tmp_path / "schemap.yaml"
    db_path = tmp_path / "test.db"

    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT);")
    cursor.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL);")
    conn.commit()
    conn.close()

    config_content = f"""database:
  connection_url: "sqlite:///{str(db_path).replace('\\', '/')}"
output:
  file_path: "./schemap_database_context.md"
  format: "markdown"
"""
    config_path.write_text(config_content, encoding="utf-8")

    # Run schemap context
    context_res = runner.invoke(cli, ["context", "--config", str(config_path)])
    assert context_res.exit_code == 0
    assert "Verifying license tier... OK" in context_res.output
    assert Path("schemap_database_context.md").exists()

    # -------------------------------------------------------------------------
    # STEP 7: Verify Subscription Lifecycle (Revocation)
    # -------------------------------------------------------------------------
    # Simulate charge refund / dispute webhook
    refund_event = {
        "id": "evt_refund_999",
        "type": "charge.refunded",
        "data": {
            "object": {
                "customer": "cus_e2e_founder_001"
            }
        }
    }
    client.post("/webhooks/stripe", json=refund_event)

    # Force bypass cache to trigger online verification check
    mocker.patch("schemap.license._read_cache", return_value=None)
    
    context_blocked_res = runner.invoke(cli, ["context", "--config", str(config_path)])
    assert context_blocked_res.exit_code == 1
    assert "License verification failed: License revoked or expired" in context_blocked_res.output
