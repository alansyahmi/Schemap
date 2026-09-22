import pytest
from benchmarks.run_n50_benchmark import run_benchmark


def test_n50_benchmark_execution():
    """Validates that the N=50 benchmark runs cleanly and asserts key invariants."""
    res = run_benchmark()
    assert res["total_tasks"] == 50

    # Ensure all strata are evaluated
    assert set(res["strata"].keys()) == {"tenant", "soft-delete", "units", "joins", "mutations"}

    # Assert 100% of mutations are blocked in Condition B
    assert res["strata"]["mutations"]["condition_b_passed"] == res["strata"]["mutations"]["total"] == 8

    # Assert Grounded Condition B passes 100% of gold checks
    assert res["condition_b_grounded"]["passed"] == 50
    assert res["condition_b_grounded"]["accuracy_pct"] == 100.0

    # Assert Baseline Condition A fails majority due to lack of grounding
    assert res["condition_a_raw"]["accuracy_pct"] < 25.0
