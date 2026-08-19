import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Tuple, Dict, Any

from .license import get_app_dir

STATE_FILE = get_app_dir() / "state.json"
TRIAL_DURATION_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _get_trial_signature(started_at: int) -> str:
    payload = f"schemap_trial::{started_at}::salt_v1_free_launch"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_state() -> Dict[str, Any]:
    """Load persistent CLI state from local app data directory."""
    if not STATE_FILE.exists():
        return {
            "run_count": 0,
            "review_prompted": False,
            "trial_started_at": None,
            "trial_signature": None,
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "run_count": 0,
            "review_prompted": False,
            "trial_started_at": None,
            "trial_signature": None,
        }


def save_state(state: Dict[str, Any]) -> None:
    """Save persistent CLI state to local app data directory."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def get_trial_status() -> Tuple[bool, int, str]:
    """
    Returns (is_active, days_remaining, status_message).
    """
    state = load_state()
    started_at = state.get("trial_started_at")
    signature = state.get("trial_signature")

    if not started_at:
        return False, 0, "not_started"

    # Validate tamper signature
    if signature != _get_trial_signature(started_at):
        return False, 0, "invalid"

    now = int(time.time())
    elapsed = now - started_at

    if elapsed > TRIAL_DURATION_SECONDS:
        return False, 0, "expired"

    remaining_seconds = TRIAL_DURATION_SECONDS - elapsed
    days_remaining = max(1, int(remaining_seconds / 86400.0) + (1 if remaining_seconds % 86400 > 0 else 0))
    return True, days_remaining, "active"


def start_trial() -> Tuple[bool, str]:
    """
    Starts a 7-day Pro trial. Returns (success, message).
    """
    state = load_state()
    started_at = state.get("trial_started_at")

    if started_at:
        is_active, days_rem, status = get_trial_status()
        if is_active:
            return False, f"Trial already active ({days_rem} days remaining)."
        return False, "Trial has already been used on this device."

    now = int(time.time())
    state["trial_started_at"] = now
    state["trial_signature"] = _get_trial_signature(now)
    save_state(state)
    return True, "7-day Free Pro trial successfully started!"


def record_successful_run(command_name: str) -> bool:
    """
    Increments successful run count and returns True if eligible for a review prompt.
    Prompt condition: exactly on run #2 or #3 and not previously prompted.
    """
    state = load_state()
    state["run_count"] = state.get("run_count", 0) + 1
    run_count = state["run_count"]
    review_prompted = state.get("review_prompted", False)
    save_state(state)

    if not review_prompted and run_count in (2, 3):
        return True
    return False


def mark_review_prompted() -> None:
    """Sets review_prompted to True so user is never interrupted again."""
    state = load_state()
    state["review_prompted"] = True
    save_state(state)
