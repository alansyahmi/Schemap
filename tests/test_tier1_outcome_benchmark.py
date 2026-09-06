"""Automated regression tests for Tier 1 Agent Task Outcome Benchmark."""

from benchmarks.tier1_outcome_benchmark import run_tier1_outcome_benchmark


def test_tier1_outcome_benchmark_execution():
    """Verify Tier 1 outcome benchmark executes across all 10 realistic developer tasks."""
    data = run_tier1_outcome_benchmark(runs_per_task=1)

    assert "status" in data
    assert "timestamp" in data

    if data["status"] == "BENCHMARK NOT RUN":
        assert "reason" in data
        assert "API" in data["reason"]
    else:
        assert data["status"] == "COMPLETED"
        assert "summary_by_mode" in data
        summary = data["summary_by_mode"]
        assert "Schemap" in summary

