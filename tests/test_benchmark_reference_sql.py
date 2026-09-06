"""Database reference validation test suite.

Verifies that all 10 task ground truth SQL queries and canonical database schemas
(Chinook, Northwind, Pagila, SaaS E-Commerce) execute without errors against SQLite.
"""

from benchmarks.tier1_outcome_benchmark import DEVELOPER_TASKS, init_in_memory_db


def test_reference_sql_query_execution():
    """Verify ground truth SQL for all 10 tasks executes cleanly against SQLite test databases."""
    for task in DEVELOPER_TASKS:
        conn = init_in_memory_db(task["schema_name"])
        cursor = conn.cursor()
        try:
            cursor.execute(task["ground_truth_sql"].strip())
            results = cursor.fetchall()
            assert isinstance(results, list)
        finally:
            conn.close()
