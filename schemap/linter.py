from .models import DatabaseSchemaModel

def calculate_score(schema: DatabaseSchemaModel, unresolved_abbrs: list[str]) -> tuple[int, list[str]]:
    score = 100
    issues = []
    
    total_tables = len(schema.tables)
    if total_tables == 0:
        return 0, ["Database is empty"]
        
    tables_without_pk = 0
    tables_without_fk = 0
    tables_without_comments = 0
    
    for t in schema.tables:
        has_pk = any(c.primary_key for c in t.columns)
        if not has_pk:
            tables_without_pk += 1
            
        if not t.foreign_keys:
            tables_without_fk += 1
            
        if not t.description:
            tables_without_comments += 1
            
    if tables_without_comments > 0:
        pct = (tables_without_comments / total_tables)
        penalty = int(pct * 20)
        score -= penalty
        issues.append(f"[Priority 1 - Missing Documentation] {tables_without_comments} tables lack descriptions/comments (-{penalty} pts)")

    if tables_without_pk > 0:
        pct = (tables_without_pk / total_tables)
        penalty = int(pct * 25)
        score -= penalty
        issues.append(f"[Priority 2 - Primary Keys] {tables_without_pk} tables lack primary keys (-{penalty} pts)")
        
    if tables_without_fk == total_tables and total_tables > 1:
        score -= 30
        issues.append("[Priority 2 - Relationships] 0 foreign keys found. Foreign keys must be defined (-30 pts)")
    elif tables_without_fk > 0:
        pct = (tables_without_fk / total_tables)
        penalty = int(pct * 15)
        score -= penalty
        issues.append(f"[Priority 2 - Disconnected Entities] {tables_without_fk} tables have no foreign keys (-{penalty} pts)")
        
    if unresolved_abbrs:
        count = len(unresolved_abbrs)
        penalty = min(count * 2, 20)
        score -= penalty
        issues.append(f"[Priority 3 - Ambiguous Naming] {count} unresolved abbreviations detected: {', '.join(unresolved_abbrs[:5])}{'...' if count > 5 else ''} (-{penalty} pts)")
        
    score = max(0, score)
    return score, issues
