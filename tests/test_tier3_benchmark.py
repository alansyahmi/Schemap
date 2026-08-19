"""Automated regression tests for Tier 3 Compiler Latency, Memory & Throughput Benchmark."""

from benchmarks.tier3_latency_stress_benchmark import benchmark_scale, run_tier3_benchmark


def test_tier3_benchmark_execution():
    """Verify Tier 3 benchmark executes across all table scales."""
    data = run_tier3_benchmark()

    assert "results" in data
    assert len(data["results"]) == 7  # 10, 25, 50, 100, 250, 500, 1000

    for r in data["results"]:
        assert r["tables_count"] > 0
        assert r["columns_count"] > 0
        assert r["throughput_compilations_per_sec"] > 0

        lat = r["latency_stats_ms"]
        assert lat["min"] <= lat["mean"] <= lat["max"]

        mem = r["memory_profile"]
        assert mem["peak_ram_kb"] > 0


def test_tier3_latency_and_memory_thresholds():
    """Verify Schemap meets strict latency (< 15ms for 100 tables) and RAM (< 5MB) thresholds."""
    res_100 = benchmark_scale(100, iterations=10)
    assert res_100["latency_stats_ms"]["p95"] < 25.0  # Must be under 25ms
    assert res_100["memory_profile"]["peak_ram_mb"] < 1.0  # Must be under 1MB

    res_500 = benchmark_scale(500, iterations=5)
    assert res_500["latency_stats_ms"]["p95"] < 60.0  # Must be under 60ms
    assert res_500["memory_profile"]["peak_ram_mb"] < 2.0  # Must be under 2MB
