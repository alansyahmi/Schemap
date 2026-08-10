import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .config import settings, validate_production_config
from .database import init_db, get_db, License
from .security import hash_license_key
from .stripe_handler import verify_and_parse_webhook, handle_stripe_event

# Simple In-Memory Rate Limiter for verification endpoint (60 requests per minute per IP)
_RATE_LIMIT_STORE: Dict[str, list[float]] = {}
RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW = 60.0

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = _RATE_LIMIT_STORE.get(client_ip, [])
    # Filter timestamps within window
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Please try again in a minute.")
    timestamps.append(now)
    _RATE_LIMIT_STORE[client_ip] = timestamps

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_config()
    init_db()
    yield

app = FastAPI(
    title="Schemap License Backend Server",
    description="Automated Stripe fulfillment, key generation, and CLI license verification API.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "schemap-license-server", "version": "1.0.0", "env": settings.ENVIRONMENT}

class LicenseVerifyRequest(BaseModel):
    license_key: str
    instance_name: Optional[str] = None

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload_bytes = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event_dict = verify_and_parse_webhook(payload_bytes, sig_header)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook parsing error: {str(e)}")
        
    try:
        result = handle_stripe_event(event_dict, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Webhook processing error: {str(e)}")

@app.post("/v1/licenses/verify")
def verify_license(req: LicenseVerifyRequest, request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    check_rate_limit(request)
    
    raw_key = req.license_key.strip()
    if not raw_key:
        return {"activated": False, "error": "Invalid license key format."}

    key_hash = hash_license_key(raw_key)
    license_obj = db.query(License).filter(License.key_hash == key_hash).first()
    
    if not license_obj:
        return {"activated": False, "error": "Invalid or expired license key."}

    now = datetime.now(timezone.utc)
    
    # 1. Check Revoked / Expired status
    if license_obj.status in ("revoked", "expired"):
        return {"activated": False, "error": "License revoked or expired."}

    # 2. Check Past Due status (7-day grace period)
    if license_obj.status == "past_due":
        updated_at = license_obj.updated_at or license_obj.created_at
        if updated_at and updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        grace_until = (updated_at or now) + timedelta(days=7)
        if now > grace_until:
            return {"activated": False, "error": "License suspended due to payment failure."}

    # 3. Check Date Expiration (Canceled or Term Subscriptions)
    expires_at = license_obj.expires_at
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            license_obj.status = "expired"
            db.commit()
            return {"activated": False, "error": "License subscription period has expired."}

    # Record Verification Audit
    license_obj.last_verified_at = now
    if req.instance_name:
        license_obj.last_instance_name = req.instance_name[:255]
    db.commit()

    return {
        "activated": True,
        "tier": license_obj.plan_tier,
        "plan": license_obj.billing_mode,
        "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None
    }
