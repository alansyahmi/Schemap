import pytest
import os
import json
from pathlib import Path
from click.testing import CliRunner

from schemap.license import (
    resolve_license_key,
    resolve_license_endpoint,
    save_credentials,
    load_credentials,
    clear_credentials,
    CREDENTIALS_FILE,
    CACHE_FILE,
    get_app_dir
)
from schemap.cli import cli

@pytest.fixture(autouse=True)
def clean_credentials_and_env(monkeypatch):
    monkeypatch.delenv("SCHEMAP_LICENSE_KEY", raising=False)
    clear_credentials()
    yield
    clear_credentials()

def test_resolve_license_key_priority(monkeypatch):
    # 1. Fallback to config file when nothing else set
    key, source = resolve_license_key(cli_option=None, config_key="config_key_123")
    assert key == "config_key_123"
    assert source == "config_file"

    # 2. Global credentials overrides config_key
    save_credentials("global_key_456")
    key, source = resolve_license_key(cli_option=None, config_key="config_key_123")
    assert key == "global_key_456"
    assert source == "global_credentials"

    # 3. Environment variable overrides global credentials
    monkeypatch.setenv("SCHEMAP_LICENSE_KEY", "env_key_789")
    key, source = resolve_license_key(cli_option=None, config_key="config_key_123")
    assert key == "env_key_789"
    assert source == "env_var"

    # 4. CLI option overrides environment variable
    key, source = resolve_license_key(cli_option="cli_key_999", config_key="config_key_123")
    assert key == "cli_key_999"
    assert source == "cli_option"

def test_save_and_clear_credentials():
    path = save_credentials("sch_live_abc123def456")
    assert path.exists()
    
    creds = load_credentials()
    assert creds is not None
    assert creds["license_key"] == "sch_live_abc123def456"
    
    clear_credentials()
    assert not CREDENTIALS_FILE.exists()
    assert load_credentials() is None

def test_endpoint_resolution_uses_saved_endpoint(monkeypatch):
    save_credentials("sch_live_endpoint_test", "https://staging-api.schemap.com/v1/licenses/verify")
    assert resolve_license_endpoint("https://config.example/verify") == "https://staging-api.schemap.com/v1/licenses/verify"
    monkeypatch.setenv("SCHEMAP_LICENSE_ENDPOINT", "https://env.example/verify")
    assert resolve_license_endpoint("https://config.example/verify") == "https://env.example/verify"

def test_cli_activate_success(mocker):
    mock_urlopen = mocker.patch('urllib.request.urlopen')
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "activated": True,
        "plan": "pro"
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["activate", "sch_live_0123456789abcdef0123456789abcdef"])
    
    assert result.exit_code == 0
    assert "License activated successfully" in result.output
    assert CREDENTIALS_FILE.exists()
    
    creds = load_credentials()
    assert creds["license_key"] == "sch_live_0123456789abcdef0123456789abcdef"

def test_cli_activate_failure(mocker):
    mock_urlopen = mocker.patch('urllib.request.urlopen')
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = json.dumps({
        "activated": False,
        "error": "Invalid key signature"
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["activate", "sch_live_invalid"])
    
    assert result.exit_code == 1
    assert "License activation failed" in result.output
    assert not CREDENTIALS_FILE.exists()

def test_cli_status_and_logout(mocker):
    runner = CliRunner()
    
    # 1. Check status on Free Tier (no credentials)
    res_free = runner.invoke(cli, ["status"])
    assert res_free.exit_code == 0
    assert "Free Tier" in res_free.output
    assert "Key Source:       None" in res_free.output

    # 2. Save credentials and check Pro status
    save_credentials("sch_live_abcdef1234567890")
    res_pro = runner.invoke(cli, ["status"])
    assert res_pro.exit_code == 0
    assert "Pro" in res_pro.output
    assert "Key Source:       global_credentials" in res_pro.output

    # 3. Logout
    res_logout = runner.invoke(cli, ["logout"])
    assert res_logout.exit_code == 0
    assert "Successfully logged out" in res_logout.output
    assert not CREDENTIALS_FILE.exists()
