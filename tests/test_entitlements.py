"""Tests for True Entitlements, Plan Gating & Feature Enforcement."""

import os
import pytest
from unittest.mock import patch, MagicMock
from schemap.license import (
    verify_tier,
    _read_cache,
    _write_cache,
    _get_signature,
    LicenseError,
    fetch_seats_status,
    deactivate_license_online,
    create_customer_portal_session
)


def test_free_tier_entitlements():
    """Verify Free tier is allowed for basic local context under limit but blocked for Team features."""
    # Allowed for basic local compilation under limit
    tier = verify_tier(tables_count=50, license_key=None)
    assert tier == "free"

    # Blocked if over table limit
    with pytest.raises(LicenseError, match="Free tier limited to 100 tables"):
        verify_tier(tables_count=150, license_key=None)

    # Blocked for CI
    with pytest.raises(LicenseError, match="Schemap Team License required for CI/CD"):
        verify_tier(tables_count=10, license_key=None, required_feature="ci")

    # Blocked for Quality Gate
    with pytest.raises(LicenseError, match="Feature 'gate' requires Schemap Team"):
        verify_tier(tables_count=10, license_key=None, required_feature="gate")

    # Blocked for Sanitize
    with pytest.raises(LicenseError, match="Feature 'sanitize' requires Schemap Team"):
        verify_tier(tables_count=10, license_key=None, required_feature="sanitize")

    # Blocked for Watch daemon
    with pytest.raises(LicenseError, match="Feature 'watch' requires Schemap Team"):
        verify_tier(tables_count=10, license_key=None, required_feature="watch")

    # Blocked for ROI Dashboard
    with pytest.raises(LicenseError, match="Feature 'roi' requires Schemap Team"):
        verify_tier(tables_count=10, license_key=None, required_feature="roi")


def test_pro_tier_entitlements():
    """Verify Pro tier is allowed for unlimited tables but blocked for Team features (Gate, CI, Watch, ROI, Sanitize)."""
    # Write a Pro tier cached license
    _write_cache("PRO-TEST-KEY", plan_tier="pro")

    # Pro allows unlimited tables locally
    tier = verify_tier(tables_count=500, license_key="PRO-TEST-KEY")
    assert tier == "pro"

    # Pro is blocked for Gate
    with pytest.raises(LicenseError, match="Feature 'gate' requires Schemap Team tier"):
        verify_tier(tables_count=10, license_key="PRO-TEST-KEY", required_feature="gate")

    # Pro is blocked for CI mode
    with pytest.raises(LicenseError, match="Feature 'ci' requires Schemap Team tier"):
        verify_tier(tables_count=10, license_key="PRO-TEST-KEY", required_feature="ci")

    # Pro is blocked for Sanitize
    with pytest.raises(LicenseError, match="Feature 'sanitize' requires Schemap Team tier"):
        verify_tier(tables_count=10, license_key="PRO-TEST-KEY", required_feature="sanitize")

    # Pro is blocked for Watch
    with pytest.raises(LicenseError, match="Feature 'watch' requires Schemap Team tier"):
        verify_tier(tables_count=10, license_key="PRO-TEST-KEY", required_feature="watch")

    # Pro is blocked for ROI
    with pytest.raises(LicenseError, match="Feature 'roi' requires Schemap Team tier"):
        verify_tier(tables_count=10, license_key="PRO-TEST-KEY", required_feature="roi")


def test_team_tier_entitlements():
    """Verify Team tier unlocks all advanced features."""
    _write_cache("TEAM-TEST-KEY", plan_tier="team")

    assert verify_tier(tables_count=500, license_key="TEAM-TEST-KEY", required_feature="gate") == "team"
    assert verify_tier(tables_count=500, license_key="TEAM-TEST-KEY", required_feature="ci") == "team"
    assert verify_tier(tables_count=500, license_key="TEAM-TEST-KEY", required_feature="sanitize") == "team"
    assert verify_tier(tables_count=500, license_key="TEAM-TEST-KEY", required_feature="watch") == "team"
    assert verify_tier(tables_count=500, license_key="TEAM-TEST-KEY", required_feature="roi") == "team"


def test_cache_preserves_plan_tier():
    """Verify license cache tamper-protection and plan_tier serialization."""
    _write_cache("KEY-ABC", plan_tier="team")
    ts, tier = _read_cache("KEY-ABC")
    assert ts is not None
    assert tier == "team"

    # Mismatched key returns None
    ts2, tier2 = _read_cache("DIFFERENT-KEY")
    assert ts2 is None
    assert tier2 is None


@patch("urllib.request.urlopen")
def test_fetch_seats_status_mock(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"tier": "team", "plan": "subscription", "seats_used": 3, "max_seats": 10, "status": "active", "devices": [{"id": 1, "device_fingerprint": "abc1234567890", "instance_name": "ci-runner-1", "last_seen_at": "2026-08-27"}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    res = fetch_seats_status("TEST-KEY-123")
    assert res["tier"] == "team"
    assert res["seats_used"] == 3
    assert res["max_seats"] == 10
    assert len(res["devices"]) == 1


def test_cli_seats_command(tmp_path):
    from click.testing import CliRunner
    from schemap.cli import cli
    from schemap.license import _write_cache

    runner = CliRunner()
    _write_cache("TEST-TEAM-KEY", plan_tier="team")

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text("""
database:
  connection_url: "sqlite:///test.db"
license_key: "TEST-TEAM-KEY"
""")

    with patch("schemap.cli.fetch_seats_status") as mock_fetch:
        mock_fetch.return_value = {
            "tier": "team",
            "plan": "subscription",
            "seats_used": 2,
            "max_seats": 10,
            "status": "active",
            "devices": [
                {"id": 1, "device_fingerprint": "dev_hash_001", "instance_name": "macbook-pro", "last_seen_at": "2026-08-27"},
                {"id": 2, "device_fingerprint": "dev_hash_002", "instance_name": "github-actions-ci", "last_seen_at": "2026-08-27"}
            ]
        }
        res = runner.invoke(cli, ["seats", "--config", str(cfg_file)])
        assert res.exit_code == 0
        assert "Schemap Team Seat & Device Management" in res.output
        assert "Seats Active:     2 / 10" in res.output
        assert "macbook-pro" in res.output
        assert "github-actions-ci" in res.output


def test_cli_seats_revoke_command(tmp_path):
    from click.testing import CliRunner
    from schemap.cli import cli
    from schemap.license import _write_cache

    runner = CliRunner()
    _write_cache("TEST-TEAM-KEY", plan_tier="team")

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text("""
database:
  connection_url: "sqlite:///test.db"
license_key: "TEST-TEAM-KEY"
""")

    with patch("schemap.cli.deactivate_license_online") as mock_deactivate:
        mock_deactivate.return_value = {"valid": True, "deactivated": True}
        res = runner.invoke(cli, ["seats", "--config", str(cfg_file), "--revoke", "dev_hash_001"])
        assert res.exit_code == 0
        assert "Revoking seat for device 'dev_hash_001'" in res.output
        assert "Revoked device 'dev_hash_001' from team license" in res.output
        mock_deactivate.assert_called_once()


def test_cli_seats_portal_command(tmp_path):
    from click.testing import CliRunner
    from schemap.cli import cli
    from schemap.license import _write_cache

    runner = CliRunner()
    _write_cache("TEST-TEAM-KEY", plan_tier="team")

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text("""
database:
  connection_url: "sqlite:///test.db"
license_key: "TEST-TEAM-KEY"
""")

    with patch("schemap.cli.create_customer_portal_session") as mock_portal:
        mock_portal.return_value = {"url": "https://billing.stripe.com/session/test_123"}
        res = runner.invoke(cli, ["seats", "--config", str(cfg_file), "--portal"])
        assert res.exit_code == 0
        assert "Generating Stripe Customer Billing Portal link" in res.output
        assert "https://billing.stripe.com/session/test_123" in res.output


def test_cli_portal_command(tmp_path):
    from click.testing import CliRunner
    from schemap.cli import cli
    from schemap.license import _write_cache

    runner = CliRunner()
    _write_cache("TEST-TEAM-KEY", plan_tier="team")

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text("""
database:
  connection_url: "sqlite:///test.db"
license_key: "TEST-TEAM-KEY"
""")

    with patch("schemap.cli.create_customer_portal_session") as mock_portal:
        mock_portal.return_value = {"url": "https://billing.stripe.com/session/portal_abc"}
        res = runner.invoke(cli, ["portal", "--config", str(cfg_file), "--no-open"])
        assert res.exit_code == 0
        assert "Generating Stripe Customer Billing Portal link" in res.output
        assert "https://billing.stripe.com/session/portal_abc" in res.output


@patch("urllib.request.urlopen")
def test_create_customer_portal_session_mock(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"url": "https://billing.stripe.com/session/test_mock"}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    res = create_customer_portal_session("TEST-KEY-123")
    assert res["url"] == "https://billing.stripe.com/session/test_mock"

