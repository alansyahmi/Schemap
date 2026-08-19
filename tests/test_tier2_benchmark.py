"""Automated regression tests for Tier 2 Live AI Accuracy & Hallucination Elimination Benchmark."""

from benchmarks.tier2_live_eval import run_tier2_benchmark


def test_tier2_benchmark_execution():
    """Verify Tier 2 benchmark executes all tasks and Schemap achieves 100% pass rate."""
    data = run_tier2_benchmark()

    assert "summary_by_mode" in data
    assert data["total_tasks_evaluated"] == 9

    summary = data["summary_by_mode"]
    assert "Zero Context" in summary
    assert "Raw DDL" in summary
    assert "Schemap" in summary

    # Zero context should have 0% execution success on complex schemas
    assert summary["Zero Context"]["execution_pass_rate"] == "0.0%"

    # Schemap must achieve 100% pass rate
    assert summary["Schemap"]["execution_pass_rate"] == "100.0%"
    assert summary["Schemap"]["hallucination_rate"] == "0.0%"
    assert summary["Schemap"]["join_accuracy_rate"] == "100.0%"
