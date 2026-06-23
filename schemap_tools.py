from langchain.tools import BaseTool
from pydantic import BaseModel

class QueryDatabaseInput(BaseModel):
    query: str

class DatabaseSchemaTool(BaseTool):
    name = "database_schema_context"
    description = """
    Use this tool to understand the underlying database schema and table relationships.
    This provides critical context before writing SQL queries or data extraction scripts.
    
    Database Context:
    # Database Schema Context

This document contains a token-optimized representation of the database schema for LLM context injection.


Table: users


Columns:

- id (INTEGER): Primary key
- name (TEXT): 






    """
    args_schema: type[BaseModel] = QueryDatabaseInput

    def _run(self, query: str) -> str:
        # In a real agent, you might connect to the DB directly.
        # This tool's primary value is securely injecting the schema into the agent's context window.
        return self.description
