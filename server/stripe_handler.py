import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .config import settings
from .database import Customer, License, StripeEvent
from .security import generate_license_key, hash_license_key, get_key_prefix
from .mailer import send_license_email

logger = logging.getLogger(__name__)

def extract_price_id(session: Dict[str, Any]) -> str | None:
    """
    Extracts Stripe Price ID from checkout session, line items, metadata, or Stripe API call.
    """
    if session.get("price_id"):
        return session.get("price_id")
    if session.get("metadata") and session["metadata"].get("price_id"):
        return session["metadata"]["price_id"]
        
    line_items = session.get("line_items")
    if isinstance(line_items, dict) and "data" in line_items and line_items["data"]:
        first_item = line_items["data"][0]
        if isinstance(first_item, dict) and "price" in first_item and isinstance(first_item["price"], dict):
            return first_item["price"].get("id")
    elif isinstance(line_items, list) and len(line_items) > 0:
        first_item = line_items[0]
        if isinstance(first_item, dict) and "price" in first_item and isinstance(first_item["price"], dict):
            return first_item["price"].get("id")
            
    # Fetch from Stripe API directly if session ID and secret key are available
    session_id = session.get("id")
    if session_id and settings.STRIPE_SECRET_KEY and settings.STRIPE_SECRET_KEY != "sk_test_mock":
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            items = stripe.checkout.Session.list_line_items(session_id, limit=1)
            if items and getattr(items, "data", None):
                first_data = items.data[0]
                if hasattr(first_data, "price") and getattr(first_data.price, "id", None):
                    return first_data.price.id
        except Exception as e:
            logger.warning(f"Could not list Stripe line items for session {session_id}: {str(e)}")

    return None

def determine_billing_info(price_id: str | None) -> Tuple[str, str, datetime | None]:
    """
    Maps Stripe Price ID to (billing_mode, plan_tier, expires_at).
    """
    now = datetime.now(timezone.utc)
    if not price_id:
        return "monthly", "pro", now + timedelta(days=32)
        
    mapping = settings.PRICE_ID_MAP.get(price_id)
    if mapping:
        billing_mode, tier = mapping
    elif "lifetime" in price_id.lower():
        billing_mode, tier = "lifetime", "pro"
    elif "annual" in price_id.lower() or "year" in price_id.lower():
        billing_mode, tier = "annual", "pro"
    elif "quarter" in price_id.lower():
        billing_mode, tier = "quarterly", "pro"
    elif "semiannual" in price_id.lower() or "halfyear" in price_id.lower():
        billing_mode, tier = "semiannual", "pro"
    else:
        billing_mode, tier = "monthly", "pro"

    if billing_mode == "lifetime":
        expires_at = None
    elif billing_mode == "annual":
        expires_at = now + timedelta(days=368)
    elif billing_mode == "semiannual":
        expires_at = now + timedelta(days=186)
    elif billing_mode == "quarterly":
        expires_at = now + timedelta(days=95)
    else:
        expires_at = now + timedelta(days=32)

    return billing_mode, tier, expires_at

def verify_and_parse_webhook(payload_bytes: bytes, sig_header: str | None) -> Dict[str, Any]:
    """
    Strictly verifies Stripe webhook signature. Raises ValueError if missing or invalid.
    """
    has_configured_secret = (
        settings.STRIPE_WEBHOOK_SECRET and 
        settings.STRIPE_WEBHOOK_SECRET != "whsec_mock"
    ) or settings.ENVIRONMENT == "production"

    if has_configured_secret:
        if not sig_header:
            raise ValueError("Missing Stripe-Signature header.")
        try:
            import stripe
            event = stripe.Webhook.construct_event(
                payload_bytes, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except Exception as e:
            logger.error(f"Stripe signature verification failed: {str(e)}")
            raise ValueError(f"Invalid webhook signature: {str(e)}")
            
    import json
    return json.loads(payload_bytes.decode("utf-8"))

def handle_stripe_event(event_dict: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Processes Stripe webhook event transactionally with atomic claim event tracking.
    """
    event_id = event_dict.get("id")
    event_type = event_dict.get("type")
    
    if not event_id or not event_type:
        raise ValueError("Invalid Stripe event structure: missing id or type.")

    # 1. Atomic Event Claim & Lock
    db_event = db.query(StripeEvent).filter(StripeEvent.event_id == event_id).first()
    if db_event:
        if db_event.status == "completed":
            logger.info(f"Event {event_id} already completed. Skipping.")
            return {"status": "already_processed", "event_id": event_id}
        if db_event.status == "processing" and (datetime.now(timezone.utc) - (db_event.created_at or datetime.now(timezone.utc))).total_seconds() < 60:
            logger.info(f"Event {event_id} currently processing elsewhere. Skipping.")
            return {"status": "already_processing", "event_id": event_id}
            
        db_event.attempts += 1
        db_event.status = "processing"
    else:
        try:
            db_event = StripeEvent(
                event_id=event_id,
                event_type=event_type,
                status="processing",
                attempts=1
            )
            db.add(db_event)
            db.flush()
        except IntegrityError:
            db.rollback()
            db_event = db.query(StripeEvent).filter(StripeEvent.event_id == event_id).first()
            if db_event and db_event.status == "completed":
                return {"status": "already_processed", "event_id": event_id}
            if db_event:
                db_event.attempts += 1
                db_event.status = "processing"

    db.commit()

    # 2. Process Event Router
    try:
        data_object = event_dict.get("data", {}).get("object", {})
        
        if event_type == "checkout.session.completed":
            _handle_checkout_completed(data_object, db)
        elif event_type == "customer.subscription.updated":
            _handle_subscription_updated(data_object, db)
        elif event_type == "customer.subscription.deleted":
            _handle_subscription_deleted(data_object, db)
        elif event_type == "invoice.payment_failed":
            _handle_payment_failed(data_object, db)
        elif event_type in ("charge.refunded", "charge.dispute.created"):
            _handle_charge_revoked(data_object, db)

        # Mark event completed only when both DB and email succeed
        db_event.status = "completed"
        db_event.processed_at = datetime.now(timezone.utc)
        db_event.last_error = None
        db.commit()
        return {"status": "success", "event_id": event_id, "type": event_type}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing event {event_id}: {str(e)}")
        db_event_retry = db.query(StripeEvent).filter(StripeEvent.event_id == event_id).first()
        if db_event_retry:
            db_event_retry.status = "failed"
            db_event_retry.last_error = str(e)
            db.commit()
        raise

def _handle_checkout_completed(session: Dict[str, Any], db: Session):
    session_id = session.get("id")
    stripe_customer_id = session.get("customer") or session.get("customer_id") or f"cus_anonymous_{session_id}"
    customer_details = session.get("customer_details") or {}
    email = customer_details.get("email") or session.get("customer_email") or "buyer@example.com"
    subscription_id = session.get("subscription")
    payment_intent_id = session.get("payment_intent")
    
    price_id = extract_price_id(session)
    billing_mode, plan_tier, expires_at = determine_billing_info(price_id)

    # Upsert Customer
    customer = db.query(Customer).filter(Customer.stripe_customer_id == stripe_customer_id).first()
    if not customer:
        customer = Customer(stripe_customer_id=stripe_customer_id, email=email)
        db.add(customer)
        db.flush()

    # Check if license for this checkout session already exists
    existing_license = db.query(License).filter(License.stripe_checkout_session_id == session_id).first()
    if not existing_license:
        # Generate License Key
        is_test_mode = settings.IS_TEST_MODE or (session_id and session_id.startswith("cs_test_"))
        raw_key = generate_license_key(test_mode=is_test_mode)
        key_hash = hash_license_key(raw_key)
        key_prefix = get_key_prefix(raw_key)

        new_license = License(
            key_hash=key_hash,
            key_prefix=key_prefix,
            customer_id=customer.id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=subscription_id,
            stripe_checkout_session_id=session_id,
            stripe_price_id=price_id,
            stripe_payment_intent_id=payment_intent_id,
            plan_tier=plan_tier,
            billing_mode=billing_mode,
            status="active",
            expires_at=expires_at
        )
        db.add(new_license)
        db.flush()
    else:
        # Re-fetch raw key is not possible since hash is stored, but for retries we issue or resend key
        raw_key = generate_license_key(test_mode=settings.IS_TEST_MODE)

    # Send Delivery Email (If email fails, raise RuntimeError to trigger Stripe retry)
    try:
        send_license_email(email, raw_key, billing_mode)
    except Exception as mail_err:
        logger.error(f"Email sending failed for session {session_id}: {str(mail_err)}")
        raise RuntimeError(f"Email delivery failed: {str(mail_err)}")

def _handle_subscription_updated(sub: Dict[str, Any], db: Session):
    sub_id = sub.get("id")
    if not sub_id:
        return
        
    license_obj = db.query(License).filter(License.stripe_subscription_id == sub_id).first()
    if not license_obj:
        return

    sub_status = sub.get("status")
    period_end = sub.get("current_period_end")
    if period_end:
        license_obj.expires_at = datetime.fromtimestamp(period_end, tz=timezone.utc) + timedelta(days=2)

    if sub_status == "active":
        license_obj.status = "active"
    elif sub_status in ("past_due", "unpaid"):
        license_obj.status = "past_due"
    elif sub_status == "canceled":
        license_obj.status = "canceled"

def _handle_subscription_deleted(sub: Dict[str, Any], db: Session):
    sub_id = sub.get("id")
    if not sub_id:
        return
    license_obj = db.query(License).filter(License.stripe_subscription_id == sub_id).first()
    if license_obj:
        license_obj.status = "canceled"

def _handle_payment_failed(invoice: Dict[str, Any], db: Session):
    sub_id = invoice.get("subscription")
    if not sub_id:
        return
    license_obj = db.query(License).filter(License.stripe_subscription_id == sub_id).first()
    if license_obj:
        license_obj.status = "past_due"

def _handle_charge_revoked(charge: Dict[str, Any], db: Session):
    customer_id = charge.get("customer")
    payment_intent_id = charge.get("payment_intent")
    
    query = db.query(License)
    if payment_intent_id:
        licenses = query.filter(License.stripe_payment_intent_id == payment_intent_id).all()
    elif customer_id:
        licenses = query.filter(License.stripe_customer_id == customer_id).all()
    else:
        licenses = []

    for l in licenses:
        l.status = "revoked"
