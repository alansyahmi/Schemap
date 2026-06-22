# Database Schema Context

This document contains a token-optimized representation of the database schema for LLM context injection.


## Table: `attestation_scores`


**Columns:**

- `id` (TEXT) **[PK]**
- `attestation_id` (TEXT) *[NOT NULL]*
- `source_id` (TEXT) *[NOT NULL]*
- `attested` (INTEGER) *[NOT NULL]*
- `notes` (TEXT)


**Relations:**

- `source_id` -> `lexical_sources.id`
- `attestation_id` -> `attestation_reliability.id`



## Table: `patterns`


**Columns:**

- `id` (TEXT) **[PK]**
- `cv_notation` (TEXT) *[NOT NULL]*
- `wizen_notation` (TEXT) *[NOT NULL]*
- `example_word` (TEXT)
- `tags` (TEXT)
- `created_at` (TEXT) *[NOT NULL]*
- `description` (TEXT)




## Table: `root_pattern_forms`


**Columns:**

- `id` (TEXT) **[PK]**
- `root_id` (TEXT) *[NOT NULL]*
- `pattern_id` (TEXT) *[NOT NULL]*
- `derived_form` (TEXT) *[NOT NULL]*


**Relations:**

- `pattern_id` -> `patterns.id`
- `root_id` -> `roots_old.id`



## Table: `subentries`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT) *[NOT NULL]*
- `headword` (TEXT) *[NOT NULL]*
- `pos` (TEXT)
- `tags` (TEXT)
- `sort_order` (INTEGER) *[NOT NULL]*


**Relations:**

- `entry_id` -> `entries.id`



## Table: `phonetics`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT)
- `subentry_id` (TEXT)
- `ipa` (TEXT) *[NOT NULL]*
- `dialect` (TEXT)
- `notes` (TEXT)


**Relations:**

- `subentry_id` -> `subentries.id`
- `entry_id` -> `entries.id`



## Table: `lexical_sources`


**Columns:**

- `id` (TEXT) **[PK]**
- `name` (TEXT) *[NOT NULL]*
- `full_title` (TEXT) *[NOT NULL]*
- `author` (TEXT)
- `year` (INTEGER)
- `reliability_weight` (REAL) *[NOT NULL]*
- `source_type` (TEXT) *[NOT NULL]*
- `url` (TEXT)
- `publisher` (TEXT)




## Table: `attestation_reliability`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT) *[NOT NULL]*
- `reliability_index` (REAL) *[NOT NULL]*
- `computed_at` (TEXT) *[NOT NULL]*


**Relations:**

- `entry_id` -> `entries.id`



## Table: `dialect_variants`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT) *[NOT NULL]*
- `region` (TEXT) *[NOT NULL]*
- `variant_form` (TEXT) *[NOT NULL]*
- `notes` (TEXT)


**Relations:**

- `entry_id` -> `entries.id`



## Table: `users`


**Columns:**

- `id` (TEXT) **[PK]**
- `clerk_id` (TEXT) *[NOT NULL]*
- `email` (TEXT) *[NOT NULL]*
- `display_name` (TEXT)
- `tier` (TEXT) *[NOT NULL]*
- `ads_disabled` (INTEGER) *[NOT NULL]*
- `audio_unlocked` (INTEGER) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*




## Table: `flashcard_lists`


**Columns:**

- `id` (TEXT) **[PK]**
- `user_id` (TEXT) *[NOT NULL]*
- `name` (TEXT) *[NOT NULL]*
- `entry_ids` (TEXT) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*


**Relations:**

- `user_id` -> `users.id`



## Table: `suggested_entries`


**Columns:**

- `id` (TEXT) **[PK]**
- `submitted_by_user_id` (TEXT)
- `headword` (TEXT) *[NOT NULL]*
- `notes` (TEXT) *[NOT NULL]*
- `status` (TEXT) *[NOT NULL]*
- `vote_count` (INTEGER) *[NOT NULL]*
- `submitted_at` (TEXT) *[NOT NULL]*


**Relations:**

- `submitted_by_user_id` -> `users.id`



## Table: `votes`


**Columns:**

- `id` (TEXT) **[PK]**
- `user_id` (TEXT) *[NOT NULL]*
- `suggested_entry_id` (TEXT) *[NOT NULL]*
- `value` (INTEGER) *[NOT NULL]*
- `reason` (TEXT)
- `voted_at` (TEXT) *[NOT NULL]*


**Relations:**

- `suggested_entry_id` -> `suggested_entries.id`
- `user_id` -> `users.id`



## Table: `blog_posts`


**Columns:**

- `id` (TEXT) **[PK]**
- `slug` (TEXT) *[NOT NULL]*
- `title` (TEXT) *[NOT NULL]*
- `excerpt` (TEXT)
- `content_md` (TEXT) *[NOT NULL]*
- `author` (TEXT) *[NOT NULL]*
- `published_at` (TEXT)
- `tags` (TEXT)
- `cover_image_url` (TEXT)




## Table: `admin_config`


**Columns:**

- `id` (TEXT) **[PK]**
- `category` (TEXT) *[NOT NULL]*
- `key` (TEXT) *[NOT NULL]*
- `value` (TEXT) *[NOT NULL]*
- `sort_order` (INTEGER)
- `created_at` (TEXT)
- `updated_at` (TEXT)




## Table: `roots`


**Columns:**

- `id` (TEXT) **[PK]**
- `consonants` (TEXT) *[NOT NULL]*
- `consonant_array` (TEXT) *[NOT NULL]*
- `notes` (TEXT)
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*
- `strength` (TEXT)
- `weak_class` (TEXT)
- `gloss` (TEXT)
- `etymology` (TEXT)
- `source` (TEXT)
- `vowel_set_perf` (TEXT)
- `vowel_set_impf` (TEXT)
- `vowel_set_imp` (TEXT)
- `is_geminate` (INTEGER)
- `synonyms` (TEXT)
- `antonyms` (TEXT)
- `related_entries` (TEXT)
- `tags` (TEXT)
- `is_imala_blocked` (BOOLEAN)




## Table: `entry_diminutives`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT) *[NOT NULL]*
- `pos` (TEXT) *[NOT NULL]*
- `gender` (TEXT)
- `form` (TEXT) *[NOT NULL]*
- `pattern` (TEXT)
- `sort_order` (INTEGER) *[NOT NULL]*
- `is_preferred` (INTEGER) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*




## Table: `site_submissions`


**Columns:**

- `id` (TEXT) **[PK]**
- `kind` (TEXT) *[NOT NULL]*
- `category` (TEXT) *[NOT NULL]*
- `subject` (TEXT) *[NOT NULL]*
- `email` (TEXT)
- `message` (TEXT)
- `page_path` (TEXT)
- `page_url` (TEXT)
- `referer` (TEXT)
- `user_agent` (TEXT)
- `status` (TEXT) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*




## Table: `suffix_catalog`


**Columns:**

- `id` (TEXT) **[PK]**
- `kind` (TEXT) *[NOT NULL]*
- `suffix` (TEXT) *[NOT NULL]*
- `label` (TEXT) *[NOT NULL]*
- `sort_order` (INTEGER) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*




## Table: `suffix_catalog_seed_state`


**Columns:**

- `id` (INTEGER) **[PK]**
- `seeded_at` (TEXT) *[NOT NULL]*




## Table: `verb_morphology`


**Columns:**

- `entry_id` (TEXT) **[PK]**
- `form` (TEXT)
- `class` (TEXT)
- `weak_class` (TEXT)
- `transitivity` (TEXT)
- `perfective_3sgm` (TEXT)
- `imperfective_3sgm` (TEXT)
- `verbal_noun` (TEXT)
- `active_participle` (TEXT)
- `passive_participle` (TEXT)
- `vowel_set_perf` (TEXT)
- `vowel_set_impf` (TEXT)
- `vowel_set_impv` (TEXT)
- `type` (TEXT)
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*
- `is_imala_blocked` (BOOLEAN)


**Relations:**

- `entry_id` -> `entries.id`



## Table: `numeral_morphology`


**Columns:**

- `entry_id` (TEXT) **[PK]**
- `numeral_type` (TEXT)
- `form_attributive_short` (TEXT)
- `form_attributive_long` (TEXT)
- `ordinal_form` (TEXT)
- `adverbial_form` (TEXT)
- `fractional_form` (TEXT)
- `multiplier_form` (TEXT)
- `distributive_form` (TEXT)
- `created_at` (TEXT)
- `updated_at` (TEXT)
- `is_inflectable` (TEXT)
- `form_plural_pattern` (TEXT)
- `vowel_set_sg` (TEXT)
- `vowel_set_pl` (TEXT)
- `vowel_set_opp` (TEXT)
- `vowel_set_dual` (TEXT)
- `plural_forms` (TEXT)
- `form_attributive_short_pattern` (TEXT)
- `feminine_form` (TEXT)
- `masculine_form` (TEXT)




## Table: `entry_relationships`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT) *[NOT NULL]*
- `target_entry_id` (TEXT) *[NOT NULL]*
- `relationship_type` (TEXT) *[NOT NULL]*
- `sort_order` (INTEGER) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*


**Relations:**

- `target_entry_id` -> `entries.id`
- `entry_id` -> `entries.id`



## Table: `alternative_forms`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT) *[NOT NULL]*
- `headword` (TEXT) *[NOT NULL]*
- `type` (TEXT)
- `sort_order` (INTEGER) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*


**Relations:**

- `entry_id` -> `entries.id`



## Table: `tags`


**Columns:**

- `id` (TEXT) **[PK]**
- `name` (TEXT) *[NOT NULL]*
- `category` (TEXT)
- `description` (TEXT)
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*




## Table: `entry_tags`


**Columns:**

- `entry_id` (TEXT) **[PK]** *[NOT NULL]*
- `tag_id` (TEXT) **[PK]** *[NOT NULL]*


**Relations:**

- `tag_id` -> `tags.id`
- `entry_id` -> `entries.id`



## Table: `stems`


**Columns:**

- `stem_string` (TEXT) **[PK]**
- `class_type` (TEXT) *[NOT NULL]*
- `is_hybrid` (BOOLEAN) *[NOT NULL]*
- `root` (TEXT)
- `agentive_suffix` (TEXT)
- `tags` (TEXT)
- `source` (TEXT)
- `glosses` (TEXT)
- `etymology` (TEXT)
- `synonyms` (TEXT)
- `antonyms` (TEXT)
- `related_stems` (TEXT)
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*




## Table: `pattern_applicability`


**Columns:**

- `id` (TEXT) **[PK]**
- `pattern_id` (TEXT)
- `category` (TEXT)
- `pos` (TEXT)
- `stress` (INTEGER)
- `is_active` (BOOLEAN)
- `sort_order` (INTEGER)
- `created_at` (DATETIME)
- `updated_at` (DATETIME)
- `linguistic_role` (TEXT)
- `target_gender` (TEXT)
- `gender` (TEXT)
- `metadata` (TEXT)


**Relations:**

- `pattern_id` -> `patterns.id`



## Table: `entries`


**Columns:**

- `id` (TEXT) **[PK]**
- `headword` (TEXT) *[NOT NULL]*
- `pos` (TEXT) *[NOT NULL]*
- `gender` (TEXT)
- `root_consonants` (TEXT)
- `stem` (TEXT)
- `is_loanword` (BOOLEAN) *[NOT NULL]*
- `is_inflectable` (BOOLEAN) *[NOT NULL]*
- `source_language` (TEXT)
- `source_id` (TEXT)
- `source_citation` (TEXT)
- `source_title` (TEXT)
- `source_year` (TEXT)
- `source_page` (TEXT)
- `source_publisher` (TEXT)
- `etymology_chain` (TEXT)
- `etymology_notes` (TEXT)
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*
- `cv_pattern` (TEXT)
- `definitions` (TEXT) *[NOT NULL]*
- `usage_examples` (TEXT) *[NOT NULL]*
- `verb_class` (TEXT)
- `verb_transitivity` (TEXT)
- `verb_perfective_3sgm` (TEXT)
- `verb_imperfective_3sgm` (TEXT)
- `verb_verbal_noun` (TEXT)
- `verb_vowel_perf` (TEXT)
- `verb_vowel_impf` (TEXT)
- `verb_vowel_impv` (TEXT)
- `verb_active_ptcp` (TEXT)
- `verb_passive_ptcp` (TEXT)
- `verb_form` (TEXT)
- `verb_type` (TEXT)
- `verb_weak_class` (TEXT)
- `elative_form` (TEXT)
- `participle_type` (TEXT)
- `numeral_type` (TEXT)
- `form_attributive_short` (TEXT)
- `form_attributive_long` (TEXT)
- `numeral_ordinal` (TEXT)
- `numeral_adverbial` (TEXT)
- `numeral_fractional` (TEXT)
- `numeral_multiplier` (TEXT)
- `numeral_distributive` (TEXT)
- `source_display` (TEXT)
- `source_tooltip` (TEXT)
- `morph_pattern` (TEXT)
- `sound_suffix` (TEXT)
- `zokk_morphology` (TEXT)
- `zokk_class` (TEXT)
- `zokk_is_hybrid` (TEXT)
- `zokk_agentive_suffix` (TEXT)


**Relations:**

- `source_id` -> `lexical_sources.id`



## Table: `entries_fts`


**Columns:**

- `headword` ()




## Table: `entries_fts_data`


**Columns:**

- `id` (INTEGER) **[PK]**
- `block` (BLOB)




## Table: `entries_fts_idx`


**Columns:**

- `segid` () **[PK]** *[NOT NULL]*
- `term` () **[PK]** *[NOT NULL]*
- `pgno` ()




## Table: `entries_fts_docsize`


**Columns:**

- `id` (INTEGER) **[PK]**
- `sz` (BLOB)




## Table: `entries_fts_config`


**Columns:**

- `k` () **[PK]** *[NOT NULL]*
- `v` ()




## Table: `noun_morphology`


**Columns:**

- `entry_id` (TEXT) **[PK]**
- `gender` (TEXT)
- `noun_type` (TEXT)
- `singular_form` (TEXT)
- `plural_forms` (TEXT)
- `sound_plural` (TEXT)
- `dual_form` (TEXT)
- `diminutive_form` (TEXT)
- `collective_form` (TEXT)
- `singulative_form` (TEXT)
- `paucal_form` (TEXT)
- `augmentative_form` (TEXT)
- `paucal_pattern` (TEXT)
- `augmentative_pattern` (TEXT)
- `feminine_form` (TEXT)
- `masculine_form` (TEXT)
- `is_collective` (BOOLEAN)
- `is_singulative` (BOOLEAN)
- `created_at` (TEXT)
- `updated_at` (TEXT)
- `vowel_set_sg` (TEXT)
- `vowel_set_opp` (TEXT)
- `vowel_set_dual` (TEXT)
- `vowel_set_pl` (TEXT)
- `form_plural_pattern` (TEXT)
- `form_fem_pattern` (TEXT)
- `form_masc_pattern` (TEXT)
- `dual_pattern` (TEXT)
- `diminutive_pattern` (TEXT)
- `morph_pattern` (TEXT)
- `is_inflectable_singular` (BOOLEAN)
- `is_inflectable_plural` (BOOLEAN)
- `verbal_form` (TEXT)




## Table: `adj_morphology`


**Columns:**

- `entry_id` (TEXT) **[PK]**
- `masculine_form` (TEXT)
- `feminine_form` (TEXT)
- `plural_form` (TEXT)
- `elative_form` (TEXT)
- `elative_pattern` (TEXT)
- `gender` (TEXT)
- `created_at` (TEXT) *[NOT NULL]*
- `updated_at` (TEXT) *[NOT NULL]*
- `form_plural_pattern` (TEXT)
- `form_fem_pattern` (TEXT)
- `form_masc_pattern` (TEXT)
- `vowel_set_sg` (TEXT)
- `vowel_set_pl` (TEXT)
- `vowel_set_opp` (TEXT)
- `pattern` (TEXT)
- `has_elative` (INTEGER) *[NOT NULL]*
- `is_inflectable` (BOOLEAN)
- `dual_form` (TEXT)
- `dual_pattern` (TEXT)
- `vowel_set_dual` (TEXT)
- `diminutive_form` (TEXT)
- `diminutive_pattern` (TEXT)


**Relations:**

- `entry_id` -> `entries.id`



## Table: `participle_morphology`


**Columns:**

- `entry_id` (TEXT) **[PK]**
- `type` (TEXT)
- `gender` (TEXT)
- `is_inflectable` (BOOLEAN)
- `created_at` (TEXT)
- `updated_at` (TEXT)
- `form_plural_pattern` (TEXT)
- `form_fem_pattern` (TEXT)
- `form_masc_pattern` (TEXT)
- `verbal_form` (TEXT)




## Table: `audio_files`


**Columns:**

- `id` (TEXT) **[PK]**
- `entry_id` (TEXT)
- `subentry_id` (TEXT)
- `r2_object_key` (TEXT) *[NOT NULL]*
- `dialect` (TEXT)
- `is_ai_generated` (BOOLEAN) *[NOT NULL]*
- `duration_seconds` (REAL)
- `generated_at` (TEXT) *[NOT NULL]*


**Relations:**

- `subentry_id` -> `subentries.id`
- `entry_id` -> `entries.id`



## Table: `subscriptions`


**Columns:**

- `id` (TEXT) **[PK]**
- `user_id` (TEXT) *[NOT NULL]*
- `tier` (TEXT) *[NOT NULL]*
- `started_at` (TEXT) *[NOT NULL]*
- `expires_at` (TEXT)
- `stripe_subscription_id` (TEXT)
- `is_lifetime` (BOOLEAN) *[NOT NULL]*


**Relations:**

- `user_id` -> `users.id`



## Table: `api_keys`


**Columns:**

- `id` (TEXT) **[PK]**
- `user_id` (TEXT) *[NOT NULL]*
- `name` (TEXT) *[NOT NULL]*
- `key_hash` (TEXT) *[NOT NULL]*
- `key_prefix` (TEXT) *[NOT NULL]*
- `usage_count` (INTEGER) *[NOT NULL]*
- `rate_limit_per_month` (INTEGER) *[NOT NULL]*
- `is_active` (BOOLEAN) *[NOT NULL]*
- `created_at` (TEXT) *[NOT NULL]*
- `last_used_at` (TEXT)


**Relations:**

- `user_id` -> `users.id`


