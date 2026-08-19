"""Automated regression tests for Tier 1 Token & Cost Efficiency Benchmarks (Next-Gen AI)."""

from benchmarks.tier1_token_benchmark import run_benchmark


def test_tier1_benchmark_execution():
    """Verify Tier 1 benchmark runs across all schemas and produces valid metrics."""
    data = run_benchmark()

    assert "results" in data
    assert len(data["results"]) == 5

    for r in data["results"]:
        assert r["tables_count"] > 0
        assert r["columns_count"] > 0
        assert r["latency_ms"] < 50.0  # Must compile within 50ms locally

        cl100k = r["cl100k_tokens"]
        assert cl100k["raw_ddl"] > cl100k["schemap_context"]
        assert cl100k["tokens_saved"] > 0

        # Verify reduction percentage calculation
        reduction_num = float(cl100k["reduction_percentage"].replace("%", ""))
        assert reduction_num > 40.0

        # Verify Next-Gen Model ROI fields
        assert "next_gen_models_roi" in r
        roi_models = r["next_gen_models_roi"]
        assert "Claude Opus 5 (Anthropic)" in roi_models
        assert "GPT-5.6 Terra (OpenAI)" in roi_models
        assert roi_models["Claude Opus 5 (Anthropic)"]["annual_savings_team_5"] > 0

        # Verify multi-turn agent loop
        assert "multi_turn_agent_loop" in r
        assert r["multi_turn_agent_loop"]["task_tokens_saved"] > 0


def test_tier1_scale_compression():
    """Verify enterprise 100-table schema achieves >= 80% token reduction."""
    data = run_benchmark()
    enterprise_res = next(r for r in data["results"] if r["tables_count"] == 100)

    reduction_num = float(enterprise_res["cl100k_tokens"]["reduction_percentage"].replace("%", ""))
    assert reduction_num >= 80.0
