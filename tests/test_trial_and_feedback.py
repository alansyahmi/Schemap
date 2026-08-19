from click.testing import CliRunner
from schemap import state
from schemap.cli import cli

def test_review_prompt_tracking(tmp_path, monkeypatch):
    test_state_file = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_FILE", test_state_file)

    # Run 1: Should not prompt yet
    assert not state.record_successful_run("context")
    # Run 2: Eligible for prompt
    assert state.record_successful_run("context")
    
    # Mark prompted
    state.mark_review_prompted()
    
    # Run 3: Should not prompt anymore since review_prompted is True
    assert not state.record_successful_run("context")

def test_cli_trial_start(tmp_path, monkeypatch):
    test_state_file = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_FILE", test_state_file)
    runner = CliRunner()

    res = runner.invoke(cli, ["trial", "start"])
    assert res.exit_code == 0
    assert "Opening Pro checkout link" in res.output
    assert "https://buy.stripe.com" in res.output
