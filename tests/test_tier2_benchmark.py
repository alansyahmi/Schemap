"""Automated regression tests for Tier 2 Live AI Accuracy & Hallucination Elimination Benchmark."""

from benchmarks.tier2_live_eval import run_tier2_benchmark


def test_tier2_benchmark_execution():
    """Verify Tier 2 benchmark executes all tasks or reports credential status."""
    data = run_tier2_benchmark()

    assert "status" in data
    assert "timestamp" in data

    if data["status"] == "BENCHMARK NOT RUN":
        assert "reason" in data
        assert "credentials" in data["reason"].lower()
    else:
        assert data["status"] == "COMPLETED"
        assert "summary_by_mode" in data
        summary = data["summary_by_mode"]
        assert summary["Schemap"]["execution_pass_rate"] == "100.0%"

