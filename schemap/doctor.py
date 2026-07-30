from typing import Dict, Any, List
from .models import DatabaseSchemaModel
from .linter import calculate_score

def render_ascii_bar(score: int, width: int = 20) -> str:
    """Render a clean progress bar e.g. [##########----------] 53/100"""
    score = max(0, min(100, score))
    filled = int(round((score / 100.0) * width))
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {score}/100"

def get_doctor_report(schema_model: DatabaseSchemaModel, raw_tables: List[Dict[str, Any]], unresolved_abbrs: List[str]) -> Dict[str, Any]:
    """Generate doctor health check metrics and actionable diagnosis."""
    total_tables = len(raw_tables)
    total_fks = sum(len(t.get('foreign_keys', [])) for t in raw_tables)
    
    ai_score, categorized_issues = calculate_score(schema_model, unresolved_abbrs)
    
    return {
        "status": "ok",
        "tables_count": total_tables,
        "relationships_count": total_fks,
        "ai_readiness_score": ai_score,
        "progress_bar": render_ascii_bar(ai_score),
        "issues": categorized_issues,
        "recommendation": "Run `schemap context` to generate AI-ready database context."
    }
