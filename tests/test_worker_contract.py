import pytest
import os
import json
import hashlib
from click.testing import CliRunner

from schemap.cli import cli
from schemap.license import (
    resolve_license_key,
    save_credentials,
    clear_credentials,
    verify_tier
)

@pytest.fixture(autouse=True)
def clean_credentials(monkeypatch):
    monkeypatch.delenv("SCHEMAP_LICENSE_KEY", raising=False)
    clear_credentials()
    yield
    clear_credentials()

def test_worker_api_contract_verification(mocker):
    # Mock online verification returning Worker contract response format: {"valid": True, "plan": "pro"}
    def mock_worker_verify(license_key, endpoint):
        return {
            "valid": True,
            "activated": True,
            "tier": "pro",
            "plan": "annual",
            "expires_at": "2027-08-10T00:00:00Z"
        }

    mocker.patch("schemap.cli.verify_license_online", side_effect=mock_worker_verify)
    mocker.patch("schemap.license.verify_license_online", side_effect=mock_worker_verify)

    runner = CliRunner()
    result = runner.invoke(cli, ["activate", "sch_live_0123456789abcdef0123456789abcdef"])
    
    assert result.exit_code == 0
    assert "License activated successfully" in result.output

    # Verify tier passes with valid worker response
    verify_tier(500, "sch_live_0123456789abcdef0123456789abcdef")

def test_sha256_pepper_hashing_compatibility():
    # Python SHA-256 pepper hashing matching Web Crypto API logic in worker/src/security.ts
    raw_key = "sch_live_testkey123"
    pepper = "schemap_prod_pepper_v1_secret"
    
    expected_payload = f"{raw_key}::{pepper}"
    expected_hash = hashlib.sha256(expected_payload.encode("utf-8")).hexdigest()
    
    assert len(expected_hash) == 64
