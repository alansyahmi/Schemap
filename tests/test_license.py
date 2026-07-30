import pytest
import os
import time
import json
from pathlib import Path
from schemap.license import (
    verify_tier,
    LicenseError,
    CACHE_FILE,
    CACHE_VALID_SECONDS,
    _get_signature
)

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
    # 50 tables, no license, not CI -> should pass
    verify_tier(50, None)

def test_free_tier_blocked_tables(mock_env):
    # 51 tables, no license, not CI -> should fail
    with pytest.raises(LicenseError, match="Free tier limited to 50 tables"):
        verify_tier(51, None)

def test_ci_blocked_no_license(monkeypatch):
    monkeypatch.setenv("CI", "true")
    with pytest.raises(LicenseError, match="Schemap Pro License required"):
        verify_tier(5, None)

def test_valid_api_activation(mocker, mock_env):
    # Mock urllib response returning activated: True
    mock_urlopen = mocker.patch('urllib.request.urlopen')
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "activated": True,
        "license_key": {"status": "active"}
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    verify_tier(15, "valid_key")
    
    # Check cache was written
    assert CACHE_FILE.exists()
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    assert "last_verified" in data
    assert "signature" in data
    assert data["license_key"] == "valid_key"

def test_cache_optimization_valid(mock_env):
    # Write a valid cache from 1 hour ago
    now = int(time.time())
    last_verified = now - 3600
    data = {
        "license_key": "cached_key",
        "last_verified": last_verified,
        "signature": _get_signature(last_verified, "cached_key")
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
        
    # Should pass because of caching without making any API call
    # We do not mock urlopen here; if it tries to call API, it will fail/raise error.
    verify_tier(15, "cached_key")

def test_cache_optimization_expired(mocker, mock_env):
    # Mock urllib response returning activated: False (expired)
    mock_urlopen = mocker.patch('urllib.request.urlopen')
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "activated": False,
        "error": "License expired"
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    # Write an expired cache from 8 days ago
    now = int(time.time())
    last_verified = now - (CACHE_VALID_SECONDS + 3600)
    data = {
        "license_key": "expired_key",
        "last_verified": last_verified,
        "signature": _get_signature(last_verified, "expired_key")
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
        
    # Should perform online verification and fail since it is expired
    with pytest.raises(LicenseError, match="License verification failed: License expired"):
        verify_tier(15, "expired_key")

def test_ci_bypasses_cache(mocker, monkeypatch):
    monkeypatch.setenv("CI", "true")
    
    # Mock urllib response returning activated: True
    mock_urlopen = mocker.patch('urllib.request.urlopen')
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "activated": True,
        "license_key": {"status": "active"}
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    # Write a valid cache from 1 hour ago
    now = int(time.time())
    last_verified = now - 3600
    data = {
        "license_key": "cached_key",
        "last_verified": last_verified,
        "signature": _get_signature(last_verified, "cached_key")
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
        
    # Even with a valid cache, running in CI should force online check (calling mock_urlopen)
    verify_tier(15, "cached_key")
    assert mock_urlopen.call_count == 1
