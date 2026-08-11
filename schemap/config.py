import os
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

class ForeignKeyOverride(BaseModel):
    table: str
    column: str
    ref_table: str
    ref_column: str

class SchemapConfig(BaseModel):
    database: DatabaseConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    domain: DomainConfig = Field(default_factory=DomainConfig)
    schema_descriptions: dict[str, TableOverride] = Field(default_factory=dict)
    foreign_key_overrides: list[ForeignKeyOverride] = Field(default_factory=list)
    profiles: dict[str, dict] = Field(default_factory=dict)
    license_key: str | None = None
    license_endpoint: str | None = "https://schemap-license-api.alansyahmi2004.workers.dev/v1/licenses/verify"

def find_config_path(start_path: Path | str | None = None) -> Path | None:
    """Walk up parent directories looking for schemap.yaml or .schemap.yaml."""
    curr = Path(start_path).resolve() if start_path else Path.cwd().resolve()
    for parent in [curr] + list(curr.parents):
        for candidate in ["schemap.yaml", ".schemap.yaml"]:
            f = parent / candidate
            if f.exists() and f.is_file():
                return f
    return None

def _deep_merge(target: dict, source: dict) -> dict:
    """Recursively merge dict source into target."""
    for k, v in source.items():
        if isinstance(v, dict) and k in target and isinstance(target[k], dict):
            _deep_merge(target[k], v)
        else:
            target[k] = v
    return target

def load_config(config_path: str | None = None, profile: str | None = None) -> SchemapConfig:
    """Loads and validates the schemap configuration."""
    resolved_path = None
    if config_path and config_path != "schemap.yaml":
        resolved_path = Path(config_path)
    else:
        discovered = find_config_path()
        resolved_path = discovered if discovered else Path("schemap.yaml")
        
    if not resolved_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {resolved_path}")
        
    with open(resolved_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    if not data:
        raise ValueError("Configuration file is empty or invalid YAML.")
        
    if profile:
        profiles = data.get("profiles", {})
        if profile not in profiles:
            raise ValueError(f"Profile '{profile}' not found in configuration.")
        prof_data = profiles[profile]
        _deep_merge(data, prof_data)

    env_url = os.environ.get("SCHEMAP_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if env_url:
        if "database" not in data or not isinstance(data["database"], dict):
            data["database"] = {}
        data["database"]["connection_url"] = env_url
        
    return SchemapConfig(**data)

