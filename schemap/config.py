import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    connection_url: str
    exclude_tables: list[str] = Field(default_factory=list)

class OutputConfig(BaseModel):
    file_path: str = "./llm_data_context.md"
    format: str = "markdown"

class SchemapConfig(BaseModel):
    database: DatabaseConfig
    output: OutputConfig
    license_key: str | None = None
    license_endpoint: str | None = "https://api.lemonsqueezy.com/v1/licenses/validate"

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
