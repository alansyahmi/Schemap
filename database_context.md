# Database Context Engine Output

## Database Overview

- **Total Tables**: 39
- **Total Columns**: 380
- **Total Foreign Key Relationships**: 26

## Schema Relationship Map

```
attestation_scores (source_id) ──> lexical_sources (id)
attestation_scores (attestation_id) ──> attestation_reliability (id)
root_pattern_forms (pattern_id) ──> patterns (id)
root_pattern_forms (root_id) ──> roots_old (id)
subentries (entry_id) ──> entries (id)
phonetics (subentry_id) ──> subentries (id)
phonetics (entry_id) ──> entries (id)
attestation_reliability (entry_id) ──> entries (id)
dialect_variants (entry_id) ──> entries (id)
flashcard_lists (user_id) ──> users (id)
suggested_entries (submitted_by_user_id) ──> users (id)
votes (suggested_entry_id) ──> suggested_entries (id)
votes (user_id) ──> users (id)
verb_morphology (entry_id) ──> entries (id)
entry_relationships (target_entry_id) ──> entries (id)
entry_relationships (entry_id) ──> entries (id)
alternative_forms (entry_id) ──> entries (id)
entry_tags (tag_id) ──> tags (id)
entry_tags (entry_id) ──> entries (id)
pattern_applicability (pattern_id) ──> patterns (id)
entries (source_id) ──> lexical_sources (id)
adj_morphology (entry_id) ──> entries (id)
audio_files (subentry_id) ──> subentries (id)
audio_files (entry_id) ──> entries (id)
subscriptions (user_id) ──> users (id)
api_keys (user_id) ──> users (id)
```

## Central Tables

### `entries`
- **Connectivity Score**: 12.0 (12 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `users`
- **Connectivity Score**: 5.0 (5 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `subentries`
- **Connectivity Score**: 3.0 (3 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `attestation_scores`
- **Connectivity Score**: 2.0 (2 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `patterns`
- **Connectivity Score**: 2.0 (2 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

## Query Examples

```sql
-- Join attestation_scores with lexical_sources
SELECT *
FROM attestation_scores
JOIN lexical_sources ON attestation_scores.source_id = lexical_sources.id;
```

```sql
-- Join attestation_scores with attestation_reliability
SELECT *
FROM attestation_scores
JOIN attestation_reliability ON attestation_scores.attestation_id = attestation_reliability.id;
```

```sql
-- Join root_pattern_forms with patterns
SELECT *
FROM root_pattern_forms
JOIN patterns ON root_pattern_forms.pattern_id = patterns.id;
```

```sql
-- Join root_pattern_forms with roots_old
SELECT *
FROM root_pattern_forms
JOIN roots_old ON root_pattern_forms.root_id = roots_old.id;
```

```sql
-- Join subentries with entries
SELECT *
FROM subentries
JOIN entries ON subentries.entry_id = entries.id;
```
