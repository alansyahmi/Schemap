# AGENTS.md — Database Context

This file provides automated database context for AI agents working in this repository.

## Database Summary
- Total Tables: 39
- Key Central Tables: entries, users, subentries, attestation_scores, patterns

## Table Map
### Table: `attestation_scores`
Columns: id, attestation_id, source_id, attested, notes
Foreign Keys: source_id -> lexical_sources.id, attestation_id -> attestation_reliability.id

### Table: `patterns`
Columns: id, cv_notation, wizen_notation, example_word, tags, created_at, description

### Table: `root_pattern_forms`
Columns: id, root_id, pattern_id, derived_form
Foreign Keys: pattern_id -> patterns.id, root_id -> roots_old.id

### Table: `subentries`
Columns: id, entry_id, headword, pos, tags, sort_order
Foreign Keys: entry_id -> entries.id

### Table: `phonetics`
Columns: id, entry_id, subentry_id, ipa, dialect, notes
Foreign Keys: subentry_id -> subentries.id, entry_id -> entries.id

### Table: `lexical_sources`
Columns: id, name, full_title, author, year, reliability_weight, source_type, url, publisher

### Table: `attestation_reliability`
Columns: id, entry_id, reliability_index, computed_at
Foreign Keys: entry_id -> entries.id

### Table: `dialect_variants`
Columns: id, entry_id, region, variant_form, notes
Foreign Keys: entry_id -> entries.id

### Table: `users`
Columns: id, clerk_id, email, display_name, tier, ads_disabled, audio_unlocked, created_at

### Table: `flashcard_lists`
Columns: id, user_id, name, entry_ids, created_at, updated_at
Foreign Keys: user_id -> users.id

### Table: `suggested_entries`
Columns: id, submitted_by_user_id, headword, notes, status, vote_count, submitted_at
Foreign Keys: submitted_by_user_id -> users.id

### Table: `votes`
Columns: id, user_id, suggested_entry_id, value, reason, voted_at
Foreign Keys: suggested_entry_id -> suggested_entries.id, user_id -> users.id

### Table: `blog_posts`
Columns: id, slug, title, excerpt, content_md, author, published_at, tags, cover_image_url

### Table: `admin_config`
Columns: id, category, key, value, sort_order, created_at, updated_at

### Table: `roots`
Columns: id, consonants, consonant_array, notes, created_at, updated_at, strength, weak_class, gloss, etymology, source, vowel_set_perf, vowel_set_impf, vowel_set_imp, is_geminate, synonyms, antonyms, related_entries, tags, is_imala_blocked

### Table: `entry_diminutives`
Columns: id, entry_id, pos, gender, form, pattern, sort_order, is_preferred, created_at, updated_at

### Table: `site_submissions`
Columns: id, kind, category, subject, email, message, page_path, page_url, referer, user_agent, status, created_at, updated_at

### Table: `suffix_catalog`
Columns: id, kind, suffix, label, sort_order, created_at, updated_at

### Table: `suffix_catalog_seed_state`
Columns: id, seeded_at

### Table: `verb_morphology`
Columns: entry_id, form, class, weak_class, transitivity, perfective_3sgm, imperfective_3sgm, verbal_noun, active_participle, passive_participle, vowel_set_perf, vowel_set_impf, vowel_set_impv, type, created_at, updated_at, is_imala_blocked
Foreign Keys: entry_id -> entries.id

### Table: `numeral_morphology`
Columns: entry_id, numeral_type, form_attributive_short, form_attributive_long, ordinal_form, adverbial_form, fractional_form, multiplier_form, distributive_form, created_at, updated_at, is_inflectable, form_plural_pattern, vowel_set_sg, vowel_set_pl, vowel_set_opp, vowel_set_dual, plural_forms, form_attributive_short_pattern, feminine_form, masculine_form

### Table: `entry_relationships`
Columns: id, entry_id, target_entry_id, relationship_type, sort_order, created_at
Foreign Keys: target_entry_id -> entries.id, entry_id -> entries.id

### Table: `alternative_forms`
Columns: id, entry_id, headword, type, sort_order, created_at
Foreign Keys: entry_id -> entries.id

### Table: `tags`
Columns: id, name, category, description, created_at, updated_at

### Table: `entry_tags`
Columns: entry_id, tag_id
Foreign Keys: tag_id -> tags.id, entry_id -> entries.id

### Table: `stems`
Columns: stem_string, class_type, is_hybrid, root, agentive_suffix, tags, source, glosses, etymology, synonyms, antonyms, related_stems, created_at, updated_at

### Table: `pattern_applicability`
Columns: id, pattern_id, category, pos, stress, is_active, sort_order, created_at, updated_at, linguistic_role, target_gender, gender, metadata
Foreign Keys: pattern_id -> patterns.id

### Table: `entries`
Columns: id, headword, pos, gender, root_consonants, stem, is_loanword, is_inflectable, source_language, source_id, source_citation, source_title, source_year, source_page, source_publisher, etymology_chain, etymology_notes, created_at, updated_at, cv_pattern, definitions, usage_examples, verb_class, verb_transitivity, verb_perfective_3sgm, verb_imperfective_3sgm, verb_verbal_noun, verb_vowel_perf, verb_vowel_impf, verb_vowel_impv, verb_active_ptcp, verb_passive_ptcp, verb_form, verb_type, verb_weak_class, elative_form, participle_type, numeral_type, form_attributive_short, form_attributive_long, numeral_ordinal, numeral_adverbial, numeral_fractional, numeral_multiplier, numeral_distributive, source_display, source_tooltip, morph_pattern, sound_suffix, zokk_morphology, zokk_class, zokk_is_hybrid, zokk_agentive_suffix
Foreign Keys: source_id -> lexical_sources.id

### Table: `entries_fts`
Columns: headword

### Table: `entries_fts_data`
Columns: id, block

### Table: `entries_fts_idx`
Columns: segid, term, pgno

### Table: `entries_fts_docsize`
Columns: id, sz

### Table: `entries_fts_config`
Columns: k, v

### Table: `noun_morphology`
Columns: entry_id, gender, noun_type, singular_form, plural_forms, sound_plural, dual_form, diminutive_form, collective_form, singulative_form, paucal_form, augmentative_form, paucal_pattern, augmentative_pattern, feminine_form, masculine_form, is_collective, is_singulative, created_at, updated_at, vowel_set_sg, vowel_set_opp, vowel_set_dual, vowel_set_pl, form_plural_pattern, form_fem_pattern, form_masc_pattern, dual_pattern, diminutive_pattern, morph_pattern, is_inflectable_singular, is_inflectable_plural, verbal_form

### Table: `adj_morphology`
Columns: entry_id, masculine_form, feminine_form, plural_form, elative_form, elative_pattern, gender, created_at, updated_at, form_plural_pattern, form_fem_pattern, form_masc_pattern, vowel_set_sg, vowel_set_pl, vowel_set_opp, pattern, has_elative, is_inflectable, dual_form, dual_pattern, vowel_set_dual, diminutive_form, diminutive_pattern
Foreign Keys: entry_id -> entries.id

### Table: `participle_morphology`
Columns: entry_id, type, gender, is_inflectable, created_at, updated_at, form_plural_pattern, form_fem_pattern, form_masc_pattern, verbal_form

### Table: `audio_files`
Columns: id, entry_id, subentry_id, r2_object_key, dialect, is_ai_generated, duration_seconds, generated_at
Foreign Keys: subentry_id -> subentries.id, entry_id -> entries.id

### Table: `subscriptions`
Columns: id, user_id, tier, started_at, expires_at, stripe_subscription_id, is_lifetime
Foreign Keys: user_id -> users.id

### Table: `api_keys`
Columns: id, user_id, name, key_hash, key_prefix, usage_count, rate_limit_per_month, is_active, created_at, last_used_at
Foreign Keys: user_id -> users.id
