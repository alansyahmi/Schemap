import secrets
import hashlib
from .config import settings

def generate_license_key(test_mode: bool = False) -> str:
    """
    Generates a cryptographically secure Schemap license key with 32 bytes (256 bits) of entropy.
    Format: sch_live_<64_hex_chars> or sch_test_<64_hex_chars>
    """
    prefix = "sch_test_" if test_mode else "sch_live_"
    entropy_hex = secrets.token_hex(32)
    return f"{prefix}{entropy_hex}"

def hash_license_key(license_key: str, pepper: str | None = None) -> str:
    """
    Computes a deterministic SHA-256 hash using the license key and server pepper.
    """
    pepper_to_use = pepper or settings.SERVER_PEPPER
    payload = f"{license_key.strip()}::{pepper_to_use}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def get_key_prefix(license_key: str) -> str:
    """
    Extracts safe prefix for display/storage (e.g. sch_live_a1b2).
    """
    cleaned = license_key.strip()
    return cleaned[:16] if len(cleaned) >= 16 else cleaned
