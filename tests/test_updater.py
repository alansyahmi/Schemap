import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from schemap.cli import cli
from schemap.updater import (
    check_for_updates,
    _parse_version,
    detect_installer,
    run_upgrade,
    detect_uninstaller,
    run_uninstall,
    purge_local_config
)


def test_parse_version():
    assert _parse_version("3.1.2") == (3, 1, 2)
    assert _parse_version("v3.2.0") == (3, 2, 0)
    assert _parse_version("4.0.0b1") == (4, 0, 0)
    assert _parse_version("3.2") == (3, 2, 0)
    assert _parse_version("3.2.0") > _parse_version("3.1.2")
    assert _parse_version("3.1.2") == _parse_version("3.1.2")
    assert _parse_version("3.1.1") < _parse_version("3.1.2")


def test_check_for_updates_available():
    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "info": {"version": "9.9.9"}
        }).encode("utf-8")
        mock_url.return_value.__enter__.return_value = mock_resp

        status = check_for_updates()
        assert status["has_update"] is True
        assert status["latest_version"] == "9.9.9"
        assert status["error"] is None


def test_check_for_updates_already_latest():
    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "info": {"version": "3.1.2"}
        }).encode("utf-8")
        mock_url.return_value.__enter__.return_value = mock_resp

        status = check_for_updates()
        assert status["has_update"] is False
        assert status["latest_version"] == "3.1.2"
        assert status["error"] is None


def test_check_for_updates_network_failure():
    with patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
        status = check_for_updates()
        assert status["has_update"] is False
        assert status["error"] is not None
        assert "timed out" in status["error"]


def test_detect_installer_pip():
    name, cmd = detect_installer()
    assert name in ["pip", "uv", "pipx"]
    assert len(cmd) >= 3


def test_cli_update_check_flag():
    runner = CliRunner()
    with patch("schemap.cli.check_for_updates") as mock_check:
        mock_check.return_value = {
            "current_version": "3.1.2",
            "latest_version": "4.0.0",
            "has_update": True,
            "error": None
        }
        result = runner.invoke(cli, ["update", "--check"])
        assert result.exit_code == 0
        assert "UPDATE AVAILABLE" in result.output
        assert "v3.1.2 -> v4.0.0" in result.output


def test_cli_update_already_latest():
    runner = CliRunner()
    with patch("schemap.cli.check_for_updates") as mock_check:
        mock_check.return_value = {
            "current_version": "3.1.2",
            "latest_version": "3.1.2",
            "has_update": False,
            "error": None
        }
        result = runner.invoke(cli, ["update"])
        assert result.exit_code == 0
        assert "already on the latest version" in result.output


def test_cli_update_perform_success():
    runner = CliRunner()
    with patch("schemap.cli.check_for_updates") as mock_check, \
         patch("schemap.cli.run_upgrade") as mock_upgrade:
        mock_check.return_value = {
            "current_version": "3.1.2",
            "latest_version": "3.2.0",
            "has_update": True,
            "error": None
        }
        mock_upgrade.return_value = (True, "Successfully installed schemap-tool-3.2.0")
        result = runner.invoke(cli, ["update"])
        assert result.exit_code == 0
        assert "Successfully updated Schemap to v3.2.0" in result.output
        mock_upgrade.assert_called_once_with(target_version="3.2.0")


def test_detect_uninstaller():
    name, cmd = detect_uninstaller()
    assert name in ["pip", "uv", "pipx"]
    assert "uninstall" in cmd


def test_cli_uninstall_aborted():
    runner = CliRunner()
    result = runner.invoke(cli, ["uninstall"], input="n\n")
    assert result.exit_code == 0
    assert "Uninstallation cancelled" in result.output


def test_cli_uninstall_confirmed_success():
    runner = CliRunner()
    with patch("schemap.cli.run_uninstall") as mock_uninst:
        mock_uninst.return_value = (True, "Successfully uninstalled schemap-tool")
        result = runner.invoke(cli, ["uninstall", "--yes"])
        assert result.exit_code == 0
        assert "Schemap CLI has been uninstalled" in result.output
        mock_uninst.assert_called_once()


def test_cli_uninstall_with_purge(tmp_path):
    runner = CliRunner()
    with patch("schemap.cli.run_uninstall") as mock_uninst, \
         patch("schemap.cli.purge_local_config") as mock_purge:
        mock_uninst.return_value = (True, "Successfully uninstalled")
        mock_purge.return_value = ["credentials.json", "license.cache"]

        result = runner.invoke(cli, ["uninstall", "--yes", "--purge"])
        assert result.exit_code == 0
        assert "Purging local configuration" in result.output
        assert "removed 2 items" in result.output
        mock_purge.assert_called_once()
        mock_uninst.assert_called_once()
