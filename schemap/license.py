import os
import time
import json
import hashlib
import urllib.request
import urllib.error
import platform
from pathlib import Path
from typing import Dict, Any

CACHE_DIR = Path.home() / ".config" / "schemap"
CACHE_FILE = CACHE_DIR / "license.cache"
CACHE_VALID_SECONDS = 7 * 24 * 60 * 60 # 7 days

class LicenseError(Exception):
    pass

def _get_signature(timestamp: int, license_key: str) -> str:
    payload = f"{license_key}::{timestamp}::schemap_salt_v2"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _read_cache(license_key: str) -> int | None:
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        last_verified = data.get("last_verified")
        signature = data.get("signature")
        cached_key = data.get("license_key")
        
        if not last_verified or not signature or cached_key != license_key:
            return None
            
        # Verify tamper signature
        expected_sig = _get_signature(last_verified, license_key)
        if signature != expected_sig:
            return None
            
        return last_verified
    except Exception:
        return None

def _write_cache(license_key: str):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        now = int(time.time())
        data = {
            "license_key": license_key,
            "last_verified": now,
            "signature": _get_signature(now, license_key)
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def verify_license_online(license_key: str, endpoint: str) -> Dict[str, Any]:
    """
    Pings Stripe to validate and activate the license key for this instance.
    """
    instance_name = os.getenv("GITHUB_RUN_ID", platform.node())
    payload = {
        "license_key": license_key,
        "instance_name": instance_name
    }
    
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"activated": False, "error": f"HTTP Error {e.code}"}
    except Exception as e:
        return {"activated": False, "error": f"Network unreachable. Cannot verify license. Details: {str(e)}"}

def verify_tier(tables_count: int, license_key: str | None, endpoint: str | None = None):
    """
    Verifies if the current usage is allowed based on the user's license tier.
    """
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    
    # 1. Block CI/CD usage on Free Tier
    if is_ci and not license_key:
        raise LicenseError("Schemap Pro License required for CI/CD pipeline automation.")
        
    # 2. Enforce Free Tier table limits
    if tables_count <= 50 and not is_ci and not license_key:
        return # allowed on free tier
        
    if not license_key:
        raise LicenseError(f"Free tier limited to 50 tables. Found {tables_count} tables. Please upgrade to Schemap Pro.")
        
    # 3. Local Cache Optimization (bypass in CI)
    if not is_ci:
        last_verified = _read_cache(license_key)
        if last_verified is not None:
            now = int(time.time())
            if now - last_verified <= CACHE_VALID_SECONDS:
                return # allowed via cached validation
                
    # 4. Perform Online Verification
    endpoint = endpoint or "https://api.stripe.com/v1/licenses/verify"
    if endpoint.endswith("/validate") or "lemonsqueezy" in endpoint:
        endpoint = "https://api.stripe.com/v1/licenses/verify"
        
    verification = verify_license_online(license_key, endpoint)
    if verification.get("activated"):
        _write_cache(license_key)
        return
    else:
        error_msg = verification.get("error", "Invalid or expired license key.")
        raise LicenseError(f"License verification failed: {error_msg}")
