import os
import sys
import stat
import time
import json
import hashlib
import urllib.request
import urllib.error
import platform
from pathlib import Path
from typing import Dict, Any, Tuple

DEFAULT_LICENSE_ENDPOINT = "https://api.schemap.com/v1/licenses/verify"
FREE_TABLE_LIMIT = 100
CACHE_VALID_SECONDS = 7 * 24 * 60 * 60 # 7 days

def get_app_dir() -> Path:
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "Schemap"
    return Path.home() / ".config" / "schemap"

CACHE_DIR = get_app_dir()
CACHE_FILE = CACHE_DIR / "license.cache"
CREDENTIALS_FILE = CACHE_DIR / "credentials.json"

class LicenseError(Exception):
    pass

def load_credentials() -> Dict[str, Any] | None:
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_credentials(license_key: str, endpoint: str | None = None) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "license_key": license_key,
        "endpoint": endpoint or DEFAULT_LICENSE_ENDPOINT,
        "activated_at": int(time.time())
    }
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if hasattr(os, "chmod") and sys.platform != "win32":
        try:
            os.chmod(CREDENTIALS_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
    return CREDENTIALS_FILE

def clear_credentials():
    if CREDENTIALS_FILE.exists():
        try:
            CREDENTIALS_FILE.unlink()
        except Exception:
            pass
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
        except Exception:
            pass

def resolve_license_key(cli_option: str | None = None, config_key: str | None = None) -> Tuple[str | None, str]:
    """
    Resolves active license key and storage source in exact order:
    1. --license-key CLI flag -> source: "cli_option"
    2. SCHEMAP_LICENSE_KEY env var -> source: "env_var"
    3. Global credentials file -> source: "global_credentials"
    4. schemap.yaml license_key field -> source: "config_file" (legacy)
    """
    if cli_option and cli_option.strip():
        return cli_option.strip(), "cli_option"

    env_key = os.getenv("SCHEMAP_LICENSE_KEY")
    if env_key and env_key.strip():
        return env_key.strip(), "env_var"

    creds = load_credentials()
    if creds and creds.get("license_key"):
        return creds["license_key"].strip(), "global_credentials"

    if config_key and config_key.strip():
        return config_key.strip(), "config_file"

    return None, "none"

def resolve_license_endpoint(config_endpoint: str | None = None, cli_endpoint: str | None = None) -> str:
    """Resolve the verification endpoint using the same global credential model."""
    if cli_endpoint and cli_endpoint.strip():
        return cli_endpoint.strip()
    env_endpoint = os.getenv("SCHEMAP_LICENSE_ENDPOINT")
    if env_endpoint and env_endpoint.strip():
        return env_endpoint.strip()
    credentials = load_credentials()
    if credentials and credentials.get("endpoint"):
        return str(credentials["endpoint"]).strip()
    return (config_endpoint or DEFAULT_LICENSE_ENDPOINT).strip()

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
    Pings Schemap license server to validate and activate the license key for this instance.
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
    # If no key was explicitly passed, resolve key via hierarchy
    if not license_key:
        resolved_key, _ = resolve_license_key(config_key=None)
        license_key = resolved_key

    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    
    # 1. Block CI/CD usage on Free Tier
    if is_ci and not license_key:
        raise LicenseError("Schemap Pro License required for CI/CD pipeline automation.")
        
    # 2. Enforce Free Tier table limits
    if tables_count <= FREE_TABLE_LIMIT and not is_ci and not license_key:
        return # allowed on free tier
        
    if not license_key:
        raise LicenseError(f"Free tier limited to {FREE_TABLE_LIMIT} tables. Found {tables_count} tables. Please upgrade to Schemap Pro.")
        
    # 3. Local Cache Optimization (bypass in CI)
    if not is_ci:
        last_verified = _read_cache(license_key)
        if last_verified is not None:
            now = int(time.time())
            if now - last_verified <= CACHE_VALID_SECONDS:
                return # allowed via cached validation
                
    # 4. Perform Online Verification
    endpoint = resolve_license_endpoint(config_endpoint=endpoint)
    if endpoint.endswith("/validate") or "lemonsqueezy" in endpoint or "stripe.com" in endpoint:
        endpoint = DEFAULT_LICENSE_ENDPOINT
        
    verification = verify_license_online(license_key, endpoint)
    if verification.get("activated"):
        _write_cache(license_key)
        return
    else:
        error_msg = verification.get("error", "Invalid or expired license key.")
        raise LicenseError(f"License verification failed: {error_msg}")
