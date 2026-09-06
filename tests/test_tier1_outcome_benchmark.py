"""Automated regression tests for Tier 1 Agent Task Outcome Benchmark."""

from benchmarks.tier1_outcome_benchmark import run_tier1_outcome_benchmark


def test_tier1_outcome_benchmark_execution():
    """Verify Tier 1 outcome benchmark executes across all 10 realistic developer tasks."""
    data = run_tier1_outcome_benchmark()

    assert "summary_by_mode" in data
    assert data["total_tasks_evaluated"] == 10
    assert "hero_question" in data

    summary = data["summary_by_mode"]
    assert "Zero Context" in summary
    assert "Raw DDL" in summary
    assert "Schemap" in summary

    # Mode C (Schemap) should have valid success metrics
    assert "first_pass_success_rate" in summary["Schemap"]
    assert "avg_tokens_per_task" in summary["Schemap"]
    assert "cost_per_task_usd" in summary["Schemap"]
