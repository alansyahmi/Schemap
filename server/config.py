import os
from pydantic_settings import BaseSettings
from typing import Dict, Tuple, List

class ServerSettings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./schemap_server.db")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "Schemap <onboarding@resend.dev>")
    SERVER_PEPPER: str = os.getenv("SERVER_PEPPER", "schemap_prod_pepper_v1_secret")
    IS_TEST_MODE: bool = os.getenv("IS_TEST_MODE", "false").lower() == "true"
    ALLOWED_ORIGINS: List[str] = [
        "https://schemap-tool.pages.dev",
        "https://schemap.com",
        "https://api.schemap.com"
    ] + (["http://localhost:8080", "http://127.0.0.1:8080"] if os.getenv("ENVIRONMENT", "development").lower() != "production" else [])
    
    # Mapping Stripe Price IDs to (billing_mode, plan_tier)
    PRICE_ID_MAP: Dict[str, Tuple[str, str]] = {
        "price_monthly": ("monthly", "pro"),
        "price_quarterly": ("quarterly", "pro"),
        "price_semiannual": ("semiannual", "pro"),
        "price_annual": ("annual", "pro"),
        "price_lifetime": ("lifetime", "pro")
    }

    class Config:
        env_file = ".env"
        extra = "allow"

settings = ServerSettings()

def validate_production_config():
    """
    Ensures mock credentials, SQLite databases, and fallback secrets cannot run in production.
    """
    if settings.ENVIRONMENT.lower() == "production":
        errors = []
        if settings.SERVER_PEPPER == "schemap_prod_pepper_v1_secret":
            errors.append("SERVER_PEPPER must be changed from default secret in production.")
        if settings.STRIPE_SECRET_KEY == "sk_test_mock" or not settings.STRIPE_SECRET_KEY.startswith("sk_"):
            errors.append("STRIPE_SECRET_KEY must be configured with a valid Stripe key in production.")
        if settings.STRIPE_WEBHOOK_SECRET == "whsec_mock" or not settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_"):
            errors.append("STRIPE_WEBHOOK_SECRET must be configured with a valid Stripe webhook secret in production.")
        if not settings.RESEND_API_KEY:
            errors.append("RESEND_API_KEY is required in production.")
        if settings.DATABASE_URL.startswith("sqlite"):
            errors.append("DATABASE_URL should use PostgreSQL in production mode (SQLite detected).")
            
        if errors:
            raise RuntimeError("Production Configuration Security Failures:\n" + "\n".join(f"- {e}" for e in errors))
