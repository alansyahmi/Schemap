import json
from .models import DatabaseSchemaModel
from .renderer import render_output

def generate_langchain(schema: DatabaseSchemaModel) -> str:
    schema_markdown = render_output(schema, fmt="markdown")
    return f'''from langchain.tools import BaseTool
from pydantic import BaseModel

class QueryDatabaseInput(BaseModel):
    query: str

class DatabaseSchemaTool(BaseTool):
    name = "database_schema_context"
    description = """
    Use this tool to understand the underlying database schema and table relationships.
    This provides critical context before writing SQL queries or data extraction scripts.
    
    Database Context:
    {schema_markdown.replace('"""', "'")}
    """
    args_schema: type[BaseModel] = QueryDatabaseInput

    def _run(self, query: str) -> str:
        # In a real agent, you might connect to the DB directly.
        # This tool's primary value is securely injecting the schema into the agent's context window.
        return self.description
'''

def generate_llamaindex(schema: DatabaseSchemaModel) -> str:
    schema_markdown = render_output(schema, fmt="markdown")
    return f'''from llama_index.core.tools import QueryEngineTool, ToolMetadata

database_schema_tool = QueryEngineTool(
    query_engine=None, # Attach your SQL query engine here
    metadata=ToolMetadata(
        name="database_schema_context",
        description="""
        Provides the schema, relationships, and business glossary for the database.
        
        {schema_markdown.replace('"""', "'")}
        """
    )
)
'''

def generate_mcp_tools(schema: DatabaseSchemaModel) -> str:
    schema_json = render_output(schema, fmt="json")
    return json.dumps({
        "tools": [
            {
                "name": "query_database_schema",
                "description": "Returns the complete database schema with tables, columns, and foreign key relationships.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                },
                "schema_payload": json.loads(schema_json)
            }
        ]
    }, indent=2)
