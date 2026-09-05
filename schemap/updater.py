import sys
import os
import shutil
import json
import subprocess
import urllib.request
from typing import Tuple, Optional, Dict, Any

from . import __version__ as CURRENT_VERSION

PYPI_PACKAGE_URL = "https://pypi.org/pypi/schemap-tool/json"
TIMEOUT_SECONDS = 4


def _parse_version(v: str) -> Tuple[int, ...]:
    """Parse version string like '3.1.2' into a comparable tuple of integers."""
    clean = v.strip().lstrip("v").split("+")[0].split("-")[0]
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def check_for_updates(timeout: int = TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Queries PyPI to check if a newer version of schemap-tool is available.
    Returns dict:
      - current_version: str
      - latest_version: str or None
      - has_update: bool
      - error: str or None
    """
    try:
        req = urllib.request.Request(
            PYPI_PACKAGE_URL,
            headers={"User-Agent": f"SchemapCLI/{CURRENT_VERSION} UpdateChecker"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latest_version = data.get("info", {}).get("version")
            if not latest_version:
                return {
                    "current_version": CURRENT_VERSION,
                    "latest_version": None,
                    "has_update": False,
                    "error": "Version info missing from PyPI response"
                }

            has_update = _parse_version(latest_version) > _parse_version(CURRENT_VERSION)
            return {
                "current_version": CURRENT_VERSION,
                "latest_version": latest_version,
                "has_update": has_update,
                "error": None
            }
    except Exception as e:
        return {
            "current_version": CURRENT_VERSION,
            "latest_version": None,
            "has_update": False,
            "error": str(e)
        }


def detect_installer() -> Tuple[str, list[str]]:
    """
    Detects the best command to update schemap-tool based on the running environment:
    - 'uv' (if uv tool or uv python env is detected)
    - 'pipx' (if pipx environment is detected)
    - 'pip' (standard pip / venv)
    Returns (installer_name, command_args).
    """
    exe_path = sys.executable.lower()

    if "pipx" in exe_path:
        pipx_bin = shutil.which("pipx")
        if pipx_bin:
            return "pipx", [pipx_bin, "upgrade", "schemap-tool"]

    if "uv" in exe_path or os.environ.get("UV_TOOL"):
        uv_bin = shutil.which("uv")
        if uv_bin:
            return "uv", [uv_bin, "tool", "upgrade", "schemap-tool"]

    # Default python -m pip upgrade
    python_bin = sys.executable
    return "pip", [python_bin, "-m", "pip", "install", "--upgrade", "schemap-tool"]


def run_upgrade(target_version: Optional[str] = None) -> Tuple[bool, str]:
    """
    Executes the self-update command using the detected package manager.
    Returns (success: bool, message: str).
    """
    installer_name, cmd = detect_installer()
    if target_version and installer_name == "pip":
        # Specific version requested
        cmd[-1] = f"schemap-tool=={target_version}"

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        output = proc.stdout.strip() if proc.stdout else ""
        if proc.returncode == 0:
            return True, output
        else:
            return False, f"Command '{' '.join(cmd)}' failed with exit code {proc.returncode}:\n{output}"
    except Exception as e:
        return False, f"Failed to execute update command '{' '.join(cmd)}': {str(e)}"
