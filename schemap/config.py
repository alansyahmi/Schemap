import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    connection_url: str
    exclude_tables: list[str] = Field(default_factory=list)

class OutputConfig(BaseModel):
    file_path: str = "./schemap_database_context.md"
    format: str = "markdown"

class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str | None = None

class DomainConfig(BaseModel):
    name: str | None = None
    mappings: dict[str, str] = Field(default_factory=dict)
    ignore_abbreviations: list[str] = Field(default_factory=list)

class ColumnOverride(BaseModel):
    description: str | None = None
    business_name: str | None = None

class TableOverride(BaseModel):
    description: str | None = None
    business_name: str | None = None
    columns: dict[str, ColumnOverride] = Field(default_factory=dict)

class SchemapConfig(BaseModel):
    database: DatabaseConfig
    output: OutputConfig
    llm: LLMConfig = Field(default_factory=LLMConfig)
    domain: DomainConfig = Field(default_factory=DomainConfig)
    schema_descriptions: dict[str, TableOverride] = Field(default_factory=dict)
    license_key: str | None = None
    license_endpoint: str | None = "https://schemap-license-api.alansyahmi2004.workers.dev/v1/licenses/verify"

def load_config(config_path: str = "schemap.yaml") -> SchemapConfig:
    """Loads and validates the schemap configuration."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(path, "r") as f:
        data = yaml.safe_load(f)
        
    if not data:
        raise ValueError("Configuration file is empty or invalid YAML.")
        
    return SchemapConfig(**data)
