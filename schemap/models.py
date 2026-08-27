from pydantic import BaseModel, Field

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

class DatabaseSchemaModel(BaseModel):
    tables: list[TableModel] = Field(default_factory=list)
    common_journeys: list[str] = Field(default_factory=list)
    glossary: dict[str, str] = Field(default_factory=dict)
    global_guardrails: list[str] = Field(default_factory=list)

