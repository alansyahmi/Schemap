from pydantic import BaseModel, Field

class ColumnModel(BaseModel):
    name: str
    data_type: str
    is_nullable: bool = True
    primary_key: bool = False
    description: str | None = None

class ForeignKeyModel(BaseModel):
    column_name: str
    foreign_table_name: str
    foreign_column_name: str

class TableModel(BaseModel):
    name: str
    description: str | None = None
    columns: list[ColumnModel] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyModel] = Field(default_factory=list)

class DatabaseSchemaModel(BaseModel):
    tables: list[TableModel] = Field(default_factory=list)
