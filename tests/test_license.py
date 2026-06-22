import pytest
import os
import time
import json
from pathlib import Path
from schemap.license import verify_tier, LicenseError, CACHE_FILE, GRACE_PERIOD_SECONDS, _get_signature

@pytest.fixture(autouse=True)
def clean_cache():
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    yield
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

def test_free_tier_allowed(mock_env):
    # 10 tables, no license, not CI -> should pass
    verify_tier(10, None)

def test_free_tier_blocked_tables(mock_env):
    # 11 tables, no license, not CI -> should fail
    with pytest.raises(LicenseError, match="Free tier limited to 10 tables"):
        verify_tier(11, None)

def test_ci_blocked_no_license(monkeypatch):
    monkeypatch.setenv("CI", "true")
    with pytest.raises(LicenseError, match="Schemap Team License required"):
        verify_tier(5, None)

def test_valid_api_call(mocker, mock_env):
    # Mock urllib to return 200
    mock_urlopen = mocker.patch('urllib.request.urlopen')
    mock_urlopen.return_value.__enter__.return_value.status = 200
    
    verify_tier(15, "valid_key")
    
    # Check cache was written
    assert CACHE_FILE.exists()
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    assert "last_verified" in data
    assert "signature" in data

def test_offline_grace_period_valid(mocker, mock_env):
    # Mock urllib to raise ConnectionError (network down)
    mocker.patch('urllib.request.urlopen', side_effect=Exception("Network down"))
    
    # Write a valid cache from 1 hour ago
    now = int(time.time())
    last_verified = now - 3600
    data = {
        "last_verified": last_verified,
        "signature": _get_signature(last_verified, "valid_key")
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
        
    # Should pass because of grace period
    verify_tier(15, "valid_key")

def test_offline_grace_period_expired(mocker, mock_env):
    # Mock urllib to raise ConnectionError (network down)
    mocker.patch('urllib.request.urlopen', side_effect=Exception("Network down"))
    
    # Write a valid cache from 73 hours ago
    now = int(time.time())
    last_verified = now - (GRACE_PERIOD_SECONDS + 3600)
    data = {
        "last_verified": last_verified,
        "signature": _get_signature(last_verified, "valid_key")
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
        
    # Should fail because grace period expired
    with pytest.raises(LicenseError, match="Offline grace period expired"):
        verify_tier(15, "valid_key")

def test_offline_tampered_cache(mocker, mock_env):
    # Mock urllib to raise ConnectionError (network down)
    mocker.patch('urllib.request.urlopen', side_effect=Exception("Network down"))
    
    # Write a tampered cache
    now = int(time.time())
    data = {
        "last_verified": now - 3600,
        "signature": "fake_bad_signature"
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
        
    # Should fail because cache signature is invalid, effectively acting like no cache exists
    with pytest.raises(LicenseError, match="Cannot verify license key"):
        verify_tier(15, "valid_key")
