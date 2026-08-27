"""
Schemap Business Semantics & Glossary Layer Engine.

Handles compiling, merging, and serializing rich business semantics:
1. Domain glossaries (business definitions and formulas).
2. Table ownership and criticality tiers.
3. Virtual / logical relationships (JOIN paths without physical database FKs).
4. Entity and column-level query guardrails.
5. Column-level semantic types and governance tags (PII, financial, immutable, etc.).
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from .models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from .config import SemanticsConfig, TableSemanticsConfig, ColumnSemanticsConfig, VirtualRelationshipConfig


def apply_semantics(schema: DatabaseSchemaModel, semantics: SemanticsConfig) -> DatabaseSchemaModel:
    """
    Applies rich business semantics, glossary, owners, tags, virtual relations, and guardrails to schema.
    """
    if not semantics:
        return schema

    # 1. Apply Glossary
    if semantics.glossary:
        schema.glossary = {**schema.glossary, **semantics.glossary}

    # 2. Apply Global Guardrails
    if semantics.global_guardrails:
        combined_rules = list(schema.global_guardrails)
        for rule in semantics.global_guardrails:
            if rule not in combined_rules:
                combined_rules.append(rule)
        schema.global_guardrails = combined_rules

    # 3. Apply Table & Column Semantics
    if semantics.tables:
        for t in schema.tables:
            if t.name in semantics.tables:
                t_cfg = semantics.tables[t.name]
                if t_cfg.description:
                    t.description = t_cfg.description
                if t_cfg.business_name:
                    t.business_name = t_cfg.business_name
                if t_cfg.owner:
                    t.owner = t_cfg.owner
                if t_cfg.criticality:
                    t.criticality = t_cfg.criticality
                if t_cfg.tags:
                    for tag in t_cfg.tags:
                        if tag not in t.tags:
                            t.tags.append(tag)
                if t_cfg.guardrails:
                    for g in t_cfg.guardrails:
                        if g not in t.guardrails:
                            t.guardrails.append(g)

                # Virtual Relationships
                if t_cfg.virtual_relationships:
                    for vr in t_cfg.virtual_relationships:
                        exists = any(
                            v.column_name == vr.column and v.foreign_table_name == vr.ref_table and v.foreign_column_name == vr.ref_column
                            for v in t.virtual_relationships
                        )
                        if not exists:
                            t.virtual_relationships.append(
                                ForeignKeyModel(
                                    column_name=vr.column,
                                    foreign_table_name=vr.ref_table,
                                    foreign_column_name=vr.ref_column
                                )
                            )

                # Columns Semantics
                if t_cfg.columns:
                    for c in t.columns:
                        if c.name in t_cfg.columns:
                            c_cfg = t_cfg.columns[c.name]
                            if c_cfg.description:
                                c.description = c_cfg.description
                            if c_cfg.business_name:
                                c.business_name = c_cfg.business_name
                            if c_cfg.semantic_type:
                                c.semantic_type = c_cfg.semantic_type
                            if c_cfg.tags:
                                for tag in c_cfg.tags:
                                    if tag not in c.tags:
                                        c.tags.append(tag)
                            if c_cfg.guardrails:
                                for g in c_cfg.guardrails:
                                    if g not in c.guardrails:
                                        c.guardrails.append(g)

    return schema


def generate_default_semantics_template(schema: DatabaseSchemaModel) -> str:
    """
    Generates a starter semantics.yaml file template populated with tables discovered in schema.
    """
    glossary = {
        "MRR": "Monthly Recurring Revenue from active customer subscriptions",
        "GMV": "Gross Merchandise Value before refunds and taxes",
        "Churn": "Customers whose subscriptions terminated within the period"
    }

    global_guardrails = [
        "All queries referencing timestamps must assume UTC",
        "Always scope tenant-isolated queries by tenant_id"
    ]

    tables_data: Dict[str, Any] = {}
    for t in schema.tables:
        t_entry: Dict[str, Any] = {
            "owner": "@engineering-team",
            "criticality": "tier-1" if any(c.primary_key for c in t.columns) else "tier-2",
            "tags": ["core"] if any(c.primary_key for c in t.columns) else [],
            "guardrails": [],
            "virtual_relationships": [],
            "columns": {}
        }
        
        for c in t.columns:
            col_lower = c.name.lower()
            tags = []
            sem_type = None
            if any(kw in col_lower for kw in ['email', 'phone', 'address', 'ssn', 'card']):
                tags.append("pii")
            if any(kw in col_lower for kw in ['cents', 'price', 'amount', 'total']):
                tags.append("financial")
                sem_type = "currency_cents"
            if 'id' in col_lower:
                tags.append("identifier")

            if tags or sem_type:
                t_entry["columns"][c.name] = {
                    "tags": tags,
                    "semantic_type": sem_type
                }
        
        tables_data[t.name] = t_entry

    payload = {
        "semantics": {
            "glossary": glossary,
            "global_guardrails": global_guardrails,
            "tables": tables_data
        }
    }

    return yaml.dump(payload, sort_keys=False, indent=2)
