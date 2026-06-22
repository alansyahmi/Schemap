import os
import time
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

CACHE_FILE = Path(".schemap_cache")
GRACE_PERIOD_SECONDS = 72 * 60 * 60  # 72 hours

class LicenseError(Exception):
    pass

def _get_signature(timestamp: int, license_key: str) -> str:
    # A simple deterministic hash to prevent obvious manual tampering
    payload = f"{license_key}::{timestamp}::schemap_salt_v1"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _read_cache(license_key: str) -> int | None:
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        last_verified = data.get("last_verified")
        signature = data.get("signature")
        
        if not last_verified or not signature:
            return None
            
        # Verify tamper signature
        expected_sig = _get_signature(last_verified, license_key)
        if signature != expected_sig:
            return None
            
        return last_verified
    except Exception:
        return None

def _write_cache(license_key: str):
    now = int(time.time())
    data = {
        "last_verified": now,
        "signature": _get_signature(now, license_key)
    }
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass # Silently fail cache writes to not disrupt the pipeline

def _validate_api(license_key: str, endpoint: str) -> bool:
    payload = json.dumps({"license_key": license_key}).encode('utf-8')
    req = urllib.request.Request(endpoint, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in (200, 201):
                # We could add deeper JSON parsing here depending on the Merchant, 
                # but a 200 OK from the validation endpoint generally indicates a valid key.
                return True
        return False
    except urllib.error.HTTPError as e:
        # 4xx or 5xx from the server means invalid key or server error
        if e.code in (400, 401, 403, 404):
            return False
        # Treat 5xx as unreachable
        raise ConnectionError("Server unreachable")
    except Exception:
        # Network down, timeout, etc
        raise ConnectionError("Network error")

def verify_tier(tables_count: int, license_key: str | None, endpoint: str | None = None):
    """
    Verifies if the current usage is allowed based on the user's license tier.
    """
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    
    # Rule 1: CI/CD Enforcement
    if is_ci and not license_key:
        raise LicenseError("Schemap Team License required for CI/CD pipeline automation.")
        
    # Rule 2: Free Tier limits
    if tables_count <= 10 and not is_ci and not license_key:
        return # allowed on free tier
        
    if not license_key:
        raise LicenseError(f"Free tier limited to 10 tables. Found {tables_count} tables. Please upgrade to Schemap Professional.")
        
    # User has a license key, let's validate it
    endpoint = endpoint or "https://api.lemonsqueezy.com/v1/licenses/validate"
    
    try:
        is_valid = _validate_api(license_key, endpoint)
        if is_valid:
            _write_cache(license_key)
            return
        else:
            raise LicenseError("Invalid license key.")
    except ConnectionError:
        # API unreachable or offline, check local cache!
        last_verified = _read_cache(license_key)
        
        if last_verified is None:
            raise LicenseError(f"Cannot verify license key (network offline). Please connect to the internet to unlock full schema access.")
            
        now = int(time.time())
        if now - last_verified <= GRACE_PERIOD_SECONDS:
            # Inside the 72 hour grace period
            import click
            click.secho("\n[Warning] Schemap could not reach validation server. Operating in offline grace period.", fg="yellow")
            return
        else:
            raise LicenseError("Offline grace period expired (>72 hours). Please check connection to unlock full schema access.")
