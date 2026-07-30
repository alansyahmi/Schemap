import time
import pytest
from pathlib import Path
from tests.stress_generator import generate_synthetic_schema_models, create_synthetic_sqlite_db
from schemap.context import generate_database_context, calculate_central_tables, generate_relationship_map
from schemap.benchmark import calculate_benchmark
from schemap.doctor import get_doctor_report

def test_stress_scale_50_tables():
    """Test performance on 50 tables."""
    schema_model = generate_synthetic_schema_models(50)
    
    t0 = time.perf_counter()
    ctx_md = generate_database_context(schema_model)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    assert len(ctx_md) > 0
    assert elapsed_ms < 500.0  # Must compile under 500ms
    print(f"\n[50 Tables] Compilation Time: {elapsed_ms:.2f} ms | Context Length: {len(ctx_md)} chars")

def test_stress_scale_200_tables():
    """Test performance scaling on 200 tables."""
    schema_model = generate_synthetic_schema_models(200)
    
    t0 = time.perf_counter()
    ctx_md = generate_database_context(schema_model)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    assert len(ctx_md) > 0
    assert elapsed_ms < 2000.0  # Must compile under 2 seconds
    print(f"\n[200 Tables] Compilation Time: {elapsed_ms:.2f} ms | Context Length: {len(ctx_md)} chars")

def test_circular_dependency_resilience():
    """Verify circular foreign key relationships (table_0 <--> table_1) do not cause infinite recursion or crash."""
    schema_model = generate_synthetic_schema_models(10)
    
    rel_map = generate_relationship_map(schema_model)
    assert len(rel_map) > 0
    
    ctx_md = generate_database_context(schema_model)
    assert "Schema Relationship Map" in ctx_md

def test_token_savings_scale():
    """Verify token reduction scaling on 100 tables."""
    schema_model = generate_synthetic_schema_models(100)
    raw_tables = [
        {"name": t.name, "columns": [{"name": c.name, "data_type": c.data_type} for c in t.columns]}
        for t in schema_model.tables
    ]
    
    bench = calculate_benchmark(schema_model, raw_tables)
    reduction = bench["context_efficiency"]["reduction_percentage"]
    reduction_val = float(reduction.replace("%", ""))
    
    assert reduction_val >= 70.0  # Token reduction must remain >= 70% even at scale
    print(f"\n[100 Tables Benchmark] Token Reduction: {reduction}")

def test_doctor_check_scale():
    """Verify schemap doctor health check runs cleanly on large schemas."""
    schema_model = generate_synthetic_schema_models(100)
    raw_tables = [
        {"name": t.name, "columns": [{"name": c.name, "data_type": c.data_type} for c in t.columns]}
        for t in schema_model.tables
    ]
    
    report = get_doctor_report(schema_model, raw_tables, unresolved_abbrs=[])
    assert report["status"] == "ok"
    assert report["tables_count"] == 100
    assert "progress_bar" in report
