import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def isolate_schemap_config_dir(tmp_path, monkeypatch):
    """
    Ensures every unit test runs against an isolated, sandbox-safe writable
    temporary directory for credentials, license caches, and device IDs.
    """
    config_dir = tmp_path / "schemap_test_config"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SCHEMAP_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("SCHEMAP_CACHE_DIR", str(config_dir))
    yield config_dir
