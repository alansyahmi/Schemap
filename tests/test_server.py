import pytest
import os
import json
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from server.app import app
from server.config import settings, validate_production_config
from server.database import Base, engine, SessionLocal, Customer, License, StripeEvent
from server.security import hash_license_key, generate_license_key
from server.stripe_handler import extract_price_id

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_mock")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_webhook_missing_signature_security(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_real_secret_12345")
    res = client.post("/webhooks/stripe", content=b'{"id":"evt_1"}', headers={})
    assert res.status_code == 400
    assert "Missing Stripe-Signature" in res.json()["detail"]

def test_webhook_invalid_signature_security(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_real_secret_12345")
    res = client.post("/webhooks/stripe", content=b'{"id":"evt_1"}', headers={"stripe-signature": "t=123,v1=invalid_sig"})
    assert res.status_code == 400
    assert "Invalid webhook signature" in res.json()["detail"]

def test_webhook_real_stripe_hmac_signature(monkeypatch, mocker):
    mock_send_email = mocker.patch("server.stripe_handler.send_license_email")
    mock_send_email.return_value = {"status": "mock_sent"}

    webhook_secret = "whsec_test_secret_key_99999"
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", webhook_secret)

    payload_data = {
        "id": "evt_signed_test_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_signed_session",
                "customer": "cus_signed_123",
                "customer_details": {"email": "signed_buyer@example.com"},
                "price_id": "price_lifetime"
            }
        }
    }
    
    mock_construct = mocker.patch("stripe.Webhook.construct_event")
    mock_construct.return_value = payload_data

    res = client.post(
        "/webhooks/stripe",
        json=payload_data,
        headers={"Content-Type": "application/json", "stripe-signature": "t=12345678,v1=valid_sig_hash"}
    )

    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert mock_send_email.call_count == 1
    assert mock_construct.call_count == 1

def test_production_config_validation(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_mock")
    with pytest.raises(RuntimeError, match="Production Configuration Security Failures"):
        validate_production_config()

def test_extract_price_id_from_line_items():
    session_with_line_items = {
        "id": "cs_123",
        "line_items": {
            "data": [
                {"price": {"id": "price_annual_pro_123"}}
            ]
        }
    }
    extracted = extract_price_id(session_with_line_items)
    assert extracted == "price_annual_pro_123"

def test_checkout_completed_lifetime(mocker):
    mock_send_email = mocker.patch("server.stripe_handler.send_license_email")
    mock_send_email.return_value = {"status": "mock_sent"}

    session_payload = {
        "id": "evt_checkout_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_session_lifetime",
                "customer": "cus_test_999",
                "customer_details": {"email": "buyer@schemap.com"},
                "price_id": "price_lifetime"
            }
        }
    }

    res = client.post("/webhooks/stripe", json=session_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    db = SessionLocal()
    customer = db.query(Customer).filter(Customer.stripe_customer_id == "cus_test_999").first()
    assert customer is not None
    assert customer.email == "buyer@schemap.com"
    db.close()

    raw_key = mock_send_email.call_args[0][1]
    verify_res = client.post("/v1/licenses/verify", json={
        "license_key": raw_key,
        "instance_name": "test-developer-laptop"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["activated"] is True

def test_idempotent_webhook(mocker):
    mock_send_email = mocker.patch("server.stripe_handler.send_license_email")
    mock_send_email.return_value = {"status": "mock_sent"}
    
    payload = {
        "id": "evt_idempotent_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_session_idempotent",
                "customer": "cus_idem_1",
                "customer_details": {"email": "idem@example.com"},
                "price_id": "price_annual"
            }
        }
    }

    res1 = client.post("/webhooks/stripe", json=payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"

    res2 = client.post("/webhooks/stripe", json=payload)
    assert res2.status_code == 200
    assert res2.json()["status"] == "already_processed"

def test_subscription_lifecycle_and_verification():
    raw_key = generate_license_key(test_mode=True)
    key_hash = hash_license_key(raw_key)
    
    db = SessionLocal()
    customer = Customer(stripe_customer_id="cus_sub_1", email="sub@example.com")
    db.add(customer)
    db.flush()
    
    license_obj = License(
        key_hash=key_hash,
        key_prefix="sch_test_sub1",
        customer_id=customer.id,
        stripe_customer_id="cus_sub_1",
        stripe_subscription_id="sub_test_001",
        stripe_checkout_session_id="cs_sub_001",
        plan_tier="pro",
        billing_mode="monthly",
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(license_obj)
    db.commit()
    db.close()

    v1 = client.post("/v1/licenses/verify", json={"license_key": raw_key})
    assert v1.json()["activated"] is True

    # Past due
    client.post("/webhooks/stripe", json={
        "id": "evt_fail_1",
        "type": "invoice.payment_failed",
        "data": {"object": {"subscription": "sub_test_001"}}
    })

    v2 = client.post("/v1/licenses/verify", json={"license_key": raw_key})
    assert v2.json()["activated"] is True

    # Refund / Revoke
    client.post("/webhooks/stripe", json={
        "id": "evt_refund_1",
        "type": "charge.refunded",
        "data": {"object": {"customer": "cus_sub_1"}}
    })

    v4 = client.post("/v1/licenses/verify", json={"license_key": raw_key})
    assert v4.json()["activated"] is False
    assert "revoked" in v4.json()["error"]
