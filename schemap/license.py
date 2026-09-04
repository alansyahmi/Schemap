import os
import sys
import stat
import time
import json
import uuid
import hashlib
import urllib.request
import urllib.error
import platform
from pathlib import Path
from typing import Dict, Any, Tuple

DEFAULT_LICENSE_ENDPOINT = "https://schemap-license-api.alansyahmi2004.workers.dev/v1/licenses/verify"
FREE_TABLE_LIMIT = 100
CACHE_VALID_SECONDS = 7 * 24 * 60 * 60 # 7 days

def get_app_dir() -> Path:
    override = os.getenv("SCHEMAP_CONFIG_DIR") or os.getenv("SCHEMAP_CACHE_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "Schemap"
    return Path.home() / ".config" / "schemap"

def get_cache_file() -> Path:
    return get_app_dir() / "license.cache"

def get_credentials_file() -> Path:
    return get_app_dir() / "credentials.json"

def get_device_id_file() -> Path:
    return get_app_dir() / "device_id"

# Module-level aliases for backward compatibility
CACHE_DIR = get_app_dir()
CACHE_FILE = get_cache_file()
CREDENTIALS_FILE = get_credentials_file()
DEVICE_ID_FILE = get_device_id_file()

def get_or_create_device_id() -> str:
    """
    Returns a stable, persistent UUID for this installation/device.
    Stored in ~/.config/schemap/device_id or APPDATA/Schemap/device_id.
    """
    dev_file = get_device_id_file()
    try:
        if dev_file.exists():
            content = dev_file.read_text(encoding="utf-8").strip()
            if content:
                return content
    except Exception:
        pass

    device_id = str(uuid.uuid4())
    try:
        get_app_dir().mkdir(parents=True, exist_ok=True)
        dev_file.write_text(device_id, encoding="utf-8")
    except Exception:
        pass
    return device_id

class LicenseError(Exception):
    pass

def load_credentials() -> Dict[str, Any] | None:
    creds_file = get_credentials_file()
    if not creds_file.exists():
        return None
    try:
        with open(creds_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_credentials(license_key: str, endpoint: str | None = None) -> Path:
    app_dir = get_app_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    creds_file = get_credentials_file()
    payload = {
        "license_key": license_key,
        "endpoint": endpoint or DEFAULT_LICENSE_ENDPOINT,
        "activated_at": int(time.time())
    }
    with open(creds_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if hasattr(os, "chmod") and sys.platform != "win32":
        try:
            os.chmod(creds_file, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
    return creds_file

def clear_credentials():
    creds_file = get_credentials_file()
    cache_file = get_cache_file()
    if creds_file.exists():
        try:
            creds_file.unlink()
        except Exception:
            pass
    if cache_file.exists():
        try:
            cache_file.unlink()
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

TIER_LEVELS = {
    "free": 0,
    "pro": 1,
    "team": 2,
    "enterprise": 3
}

FEATURE_MIN_TIERS = {
    "gate": "team",
    "ci": "team",
    "sanitize": "team",
    "watch": "team",
    "roi": "team",
    "unlimited_tables": "pro"
}

def _get_signature(timestamp: int, license_key: str, plan_tier: str = "pro") -> str:
    payload = f"{license_key}::{timestamp}::{plan_tier}::schemap_salt_v2"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _read_cache(license_key: str) -> Tuple[int | None, str | None]:
    cache_file = get_cache_file()
    if not cache_file.exists():
        return None, None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        last_verified = data.get("last_verified")
        signature = data.get("signature")
        cached_key = data.get("license_key")
        plan_tier = data.get("plan_tier", "pro")
        
        if not last_verified or not signature or cached_key != license_key:
            return None, None
            
        # Verify tamper signature (fallback to legacy signature without plan_tier if needed)
        expected_sig = _get_signature(last_verified, license_key, plan_tier)
        legacy_sig = hashlib.sha256(f"{license_key}::{last_verified}::schemap_salt_v2".encode("utf-8")).hexdigest()
        
        if signature != expected_sig and signature != legacy_sig:
            return None, None
            
        return last_verified, plan_tier
    except Exception:
        return None, None

def _write_cache(license_key: str, plan_tier: str = "pro"):
    try:
        app_dir = get_app_dir()
        app_dir.mkdir(parents=True, exist_ok=True)
        cache_file = get_cache_file()
        now = int(time.time())
        data = {
            "license_key": license_key,
            "last_verified": now,
            "plan_tier": plan_tier,
            "signature": _get_signature(now, license_key, plan_tier)
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def verify_license_online(license_key: str, endpoint: str) -> Dict[str, Any]:
    """
    Pings Schemap license server to validate and activate the license key for this instance.
    """
    instance_name = os.getenv("GITHUB_RUN_ID", platform.node())
    device_id = get_or_create_device_id()
    payload = {
        "license_key": license_key,
        "instance_name": instance_name,
        "device_id": device_id
    }
    
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SchemapCLI/3.1"
        },
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

def deactivate_license_online(license_key: str, endpoint: str, device_id_to_revoke: str | None = None) -> Dict[str, Any]:
    """
    Notifies Schemap license server to remove device seat activation for this instance or a target device ID.
    """
    deactivate_endpoint = endpoint.replace("/v1/licenses/verify", "/v1/licenses/deactivate")
    if not deactivate_endpoint.endswith("/v1/licenses/deactivate"):
        deactivate_endpoint = "https://schemap-license-api.alansyahmi2004.workers.dev/v1/licenses/deactivate"

    instance_name = os.getenv("GITHUB_RUN_ID", platform.node())
    device_id = device_id_to_revoke or get_or_create_device_id()
    payload = {
        "license_key": license_key,
        "instance_name": instance_name,
        "device_id": device_id
    }
    
    req = urllib.request.Request(
        deactivate_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SchemapCLI/3.1"
        },
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
            return {"deactivated": False, "error": f"HTTP Error {e.code}"}
    except Exception as e:
        return {"deactivated": False, "error": f"Network unreachable. Details: {str(e)}"}


def fetch_seats_status(license_key: str, endpoint: str | None = None) -> Dict[str, Any]:
    """
    Fetches team seat allocation and active seat count from license server.
    """
    base_endpoint = resolve_license_endpoint(config_endpoint=endpoint)
    seats_endpoint = base_endpoint.replace("/v1/licenses/verify", "/v1/licenses/seats")
    if not seats_endpoint.endswith("/v1/licenses/seats"):
        seats_endpoint = "https://schemap-license-api.alansyahmi2004.workers.dev/v1/licenses/seats"

    import urllib.parse
    url = f"{seats_endpoint}?license_key={urllib.parse.quote(license_key)}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "SchemapCLI/3.1"
        },
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def create_customer_portal_session(license_key: str, endpoint: str | None = None, return_url: str = "https://schemap.dev") -> Dict[str, Any]:
    """
    Requests a Stripe Customer Billing Portal session URL from the license API.
    """
    base_endpoint = resolve_license_endpoint(config_endpoint=endpoint)
    portal_endpoint = base_endpoint.replace("/v1/licenses/verify", "/v1/billing/portal")
    if not portal_endpoint.endswith("/v1/billing/portal"):
        portal_endpoint = "https://schemap-license-api.alansyahmi2004.workers.dev/v1/billing/portal"

    payload = {
        "license_key": license_key,
        "return_url": return_url
    }
    req = urllib.request.Request(
        portal_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SchemapCLI/3.1"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"error": f"HTTP Error {e.code}"}
    except Exception as e:
        return {"error": f"Network error: {str(e)}"}


def verify_tier(
    tables_count: int,
    license_key: str | None,
    endpoint: str | None = None,
    required_feature: str | None = None
) -> str:
    """
    Verifies if current usage and requested feature are entitled under the active license tier.
    Returns the verified plan tier (e.g. 'free', 'pro', 'team', 'enterprise').
    """
    # If no key was explicitly passed, resolve key via hierarchy
    if not license_key:
        resolved_key, _ = resolve_license_key(config_key=None)
        license_key = resolved_key

    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    
    # Map CI to feature requirement
    if is_ci and not required_feature:
        required_feature = "ci"

    min_required_tier = FEATURE_MIN_TIERS.get(required_feature, "pro") if required_feature else ("pro" if tables_count > FREE_TABLE_LIMIT else "free")
    min_required_level = TIER_LEVELS.get(min_required_tier, 0)

    # 1. Handle unauthenticated Free Tier
    if not license_key:
        if min_required_level > 0:
            if required_feature == "ci" or is_ci:
                raise LicenseError("Schemap Team License required for CI/CD pipeline automation. Upgrade at https://schemap.dev/#pricing")
            if required_feature:
                raise LicenseError(f"Feature '{required_feature}' requires Schemap Team tier. Upgrade at https://schemap.dev/#pricing")
            raise LicenseError(f"Free tier limited to {FREE_TABLE_LIMIT} tables. Found {tables_count} tables. Upgrade to Pro or Team at https://schemap.dev/#pricing.")
        return "free"

    # 2. Check Local Cache Optimization (bypassed in CI)
    if not is_ci:
        last_verified, cached_tier = _read_cache(license_key)
        if last_verified is not None and cached_tier:
            now = int(time.time())
            if now - last_verified <= CACHE_VALID_SECONDS:
                tier_level = TIER_LEVELS.get(cached_tier, 1)
                if tier_level < min_required_level:
                    raise LicenseError(
                        f"Feature '{required_feature}' requires Schemap {min_required_tier.title()} tier (current license: {cached_tier.title()}). "
                        f"Upgrade at https://schemap.dev/#pricing"
                    )
                return cached_tier

    # 3. Perform Online Verification
    endpoint = resolve_license_endpoint(config_endpoint=endpoint)
    if endpoint.endswith("/validate") or "lemonsqueezy" in endpoint or "stripe.com" in endpoint:
        endpoint = DEFAULT_LICENSE_ENDPOINT
        
    verification = verify_license_online(license_key, endpoint)
    if verification.get("activated") or verification.get("valid"):
        active_tier = (verification.get("tier") or verification.get("plan_tier") or "pro").lower()
        _write_cache(license_key, plan_tier=active_tier)

        tier_level = TIER_LEVELS.get(active_tier, 1)
        if tier_level < min_required_level:
            raise LicenseError(
                f"Feature '{required_feature}' requires Schemap {min_required_tier.title()} tier (current license: {active_tier.title()}). "
                f"Upgrade at https://schemap.dev/#pricing"
            )
        return active_tier
    else:
        error_msg = verification.get("error", "Invalid or expired license key.")
        raise LicenseError(f"License verification failed: {error_msg}")

