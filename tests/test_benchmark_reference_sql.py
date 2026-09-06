"""Database reference validation test suite.

Verifies that all 10 task ground truth SQL queries and canonical database schemas
(Chinook, Northwind, Pagila) execute cleanly and return non-empty datasets against seeded databases.
"""

from benchmarks.tier1_outcome_benchmark import (
    DEVELOPER_TASKS,
    init_in_memory_db,
    verify_result_correctness,
)


def test_reference_sql_query_execution_and_semantic_matching():
    """Verify ground truth SQL for all 10 tasks executes and returns non-empty results."""
    for task in DEVELOPER_TASKS:
        conn = init_in_memory_db(task["schema_name"])
        cursor = conn.cursor()
        try:
            cursor.execute(task["ground_truth_sql"].strip())
            results = cursor.fetchall()
            assert isinstance(results, list)
            assert len(results) > 0, f"Task {task['id']} returned empty results"

            # Self-comparison should be 100% semantically correct
            assert verify_result_correctness(results, results) is True

            # Modified row should fail semantic correctness
            tampered_results = results[:-1] if len(results) > 1 else [(999999,)]
            assert verify_result_correctness(tampered_results, results) is False
        finally:
            conn.close()
