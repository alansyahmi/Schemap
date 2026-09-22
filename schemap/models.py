from enum import Enum
from pydantic import BaseModel, Field

class Provenance(str, Enum):
    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"

class SemanticRole(str, Enum):
    MEASURE = "MEASURE"
    DIMENSION = "DIMENSION"
    TIME_GRAIN = "TIME_GRAIN"
    TENANT_KEY = "TENANT_KEY"
    SOFT_DELETE = "SOFT_DELETE"
    LIFECYCLE_STATE = "LIFECYCLE_STATE"
    PRIMARY_KEY = "PRIMARY_KEY"
    FOREIGN_KEY = "FOREIGN_KEY"

class ColumnModel(BaseModel):
    name: str
    data_type: str
    is_nullable: bool = True
    primary_key: bool = False
    description: str | None = None
    business_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    semantic_type: str | None = None
    guardrails: list[str] = Field(default_factory=list)
    semantic_role: SemanticRole | None = None
    provenance: Provenance = Provenance.INFERRED

class ForeignKeyModel(BaseModel):
    column_name: str
    foreign_table_name: str
    foreign_column_name: str

class TableModel(BaseModel):
    name: str
    description: str | None = None
    business_name: str | None = None
    owner: str | None = None
    criticality: str | None = None
    tags: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    columns: list[ColumnModel] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyModel] = Field(default_factory=list)
    virtual_relationships: list[ForeignKeyModel] = Field(default_factory=list)
    hierarchy_tree: str | None = None
    tenant_key: str | None = None
    soft_delete_column: str | None = None

class DatabaseSchemaModel(BaseModel):
    tables: list[TableModel] = Field(default_factory=list)
    common_journeys: list[str] = Field(default_factory=list)
    glossary: dict[str, str] = Field(default_factory=dict)
    global_guardrails: list[str] = Field(default_factory=list)

class SemanticEntity(BaseModel):
    table: str
    column: str
    role: SemanticRole
    provenance: Provenance = Provenance.INFERRED
    data_type: str
    expression: str | None = None
    description: str | None = None

class JoinStep(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    is_virtual: bool = False

class JoinPath(BaseModel):
    tables: list[str]
    steps: list[JoinStep] = Field(default_factory=list)
    sql_join_clause: str = ""

class SemanticPolicyGraph(BaseModel):
    database_name: str | None = "postgres"
    tables: dict[str, TableModel] = Field(default_factory=dict)
    tenant_keys: dict[str, str] = Field(default_factory=dict)
    soft_deletes: dict[str, str] = Field(default_factory=dict)
    lifecycle_columns: dict[str, str] = Field(default_factory=dict)
    measures: list[SemanticEntity] = Field(default_factory=list)
    dimensions: list[SemanticEntity] = Field(default_factory=list)
    provenance_map: dict[str, Provenance] = Field(default_factory=dict)
    declared_invariants: list[str] = Field(default_factory=list)

class GroundedPlan(BaseModel):
    question: str
    target_tables: list[str] = Field(default_factory=list)
    join_path: JoinPath | None = None
    mandatory_filters: list[str] = Field(default_factory=list)
    measures: list[SemanticEntity] = Field(default_factory=list)
    dimensions: list[SemanticEntity] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    prompt_instructions: str = ""

class ValidationResult(BaseModel):
    passed: bool
    violations: list[str] = Field(default_factory=list)
    patched_sql: str | None = None
    tables_analyzed: list[str] = Field(default_factory=list)

