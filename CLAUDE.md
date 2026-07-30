# Database Architecture & Context for Claude

This project relies on the database schema outlined below. Refer to this context when writing queries, migrations, or database-related business logic.

## Core Statistics
- **Active Tables**: 39
- **Key Hub Entities**: entries, users, subentries, attestation_scores, patterns

## Central Tables Overview
- **`entries`**: No description
  Columns: `id` (TEXT), `headword` (TEXT), `pos` (TEXT), `gender` (TEXT), `root_consonants` (TEXT), `stem` (TEXT) ...+47 more
- **`users`**: No description
  Columns: `id` (TEXT), `clerk_id` (TEXT), `email` (TEXT), `display_name` (TEXT), `tier` (TEXT), `ads_disabled` (INTEGER) ...+2 more
- **`subentries`**: No description
  Columns: `id` (TEXT), `entry_id` (TEXT), `headword` (TEXT), `pos` (TEXT), `tags` (TEXT), `sort_order` (INTEGER)
- **`attestation_scores`**: No description
  Columns: `id` (TEXT), `attestation_id` (TEXT), `source_id` (TEXT), `attested` (INTEGER), `notes` (TEXT)
- **`patterns`**: No description
  Columns: `id` (TEXT), `cv_notation` (TEXT), `wizen_notation` (TEXT), `example_word` (TEXT), `tags` (TEXT), `created_at` (TEXT) ...+1 more

## Schema Relationships
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
... and 16 more relationships.
```

## Query Guidelines
- Always verify foreign key constraints before building multi-table joins.
- Use standard indexed columns (`id`, `*_id`) for joins.
