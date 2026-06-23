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
            
    if tables_without_pk > 0:
        pct = (tables_without_pk / total_tables)
        penalty = int(pct * 25)
        score -= penalty
        issues.append(f"{tables_without_pk} tables lack primary keys (-{penalty} pts)")
        
    if tables_without_comments > 0:
        pct = (tables_without_comments / total_tables)
        penalty = int(pct * 20)
        score -= penalty
        issues.append(f"{tables_without_comments} tables are missing descriptions/comments (-{penalty} pts)")
        
    # A database with no foreign keys at all is a huge red flag for AI
    if tables_without_fk == total_tables and total_tables > 1:
        score -= 30
        issues.append("0 foreign keys found. Relationships must be inferred, which severely hurts AI performance (-30 pts)")
    elif tables_without_fk > 0:
        pct = (tables_without_fk / total_tables)
        penalty = int(pct * 15)
        score -= penalty
        issues.append(f"{tables_without_fk} tables have no foreign keys (disconnected entities) (-{penalty} pts)")
        
    if unresolved_abbrs:
        count = len(unresolved_abbrs)
        penalty = min(count * 2, 20) # cap at 20 points
        score -= penalty
        issues.append(f"{count} unresolved abbreviations detected: {', '.join(unresolved_abbrs[:5])}{'...' if count > 5 else ''} (-{penalty} pts)")
        
    score = max(0, score)
    return score, issues
