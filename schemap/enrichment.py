import re
import json
from .models import DatabaseSchemaModel

CORE_MAPPINGS = {
    "id": "Identifier",
    "pk": "Primary Key",
    "fk": "Foreign Key",
    "ts": "Timestamp",
    "dt": "DateTime",
    "qty": "Quantity",
    "desc": "Description",
    "addr": "Address",
    "num": "Number",
    "amt": "Amount",
    "cust": "Customer",
    "usr": "User",
    "org": "Organization",
    "loc": "Location",
    "msg": "Message",
    "img": "Image",
    "err": "Error",
    "req": "Request",
    "res": "Response",
    "stat": "Status",
    "sys": "System",
    "cfg": "Configuration",
    "val": "Value",
    "min": "Minimum",
    "max": "Maximum",
    "avg": "Average",
    "tot": "Total",
    "cnt": "Count",
    "idx": "Index",
    "ref": "Reference",
    "src": "Source",
    "dst": "Destination",
    "param": "Parameter",
    "var": "Variable",
    "str": "String",
    "bool": "Boolean",
    "int": "Integer",
    "float": "Float",
    "dict": "Dictionary",
    "obj": "Object",
    "arr": "Array",
    "guid": "Global Unique Identifier",
    "uuid": "Universally Unique Identifier",
    "ip": "IP Address",
    "url": "Uniform Resource Locator",
    "uri": "Uniform Resource Identifier",
    "pwd": "Password",
    "pw": "Password",
    "auth": "Authentication",
    "tok": "Token",
    "sess": "Session",
    "env": "Environment",
    "app": "Application",
    "db": "Database",
    "tbl": "Table",
    "col": "Column",
    "row": "Row",
    "rec": "Record",
    "doc": "Document",
    "dir": "Directory",
    "file": "File",
    "img": "Image",
    "vid": "Video",
    "aud": "Audio",
    "txt": "Text",
    "bin": "Binary",
    "hex": "Hexadecimal",
    "dec": "Decimal",
    "oct": "Octal",
    "xml": "XML",
    "json": "JSON",
    "html": "HTML",
    "css": "CSS",
    "js": "JavaScript",
    "csv": "CSV",
    "tsv": "TSV",
    "pdf": "PDF",
    "zip": "ZIP",
    "tar": "TAR",
    "gz": "GZ",
    "md": "Markdown",
    "rtf": "RTF",
    "doc": "Document",
    "xls": "Excel",
    "ppt": "PowerPoint"
}

def apply_heuristics(schema: DatabaseSchemaModel, domain_mappings: dict = None) -> tuple[DatabaseSchemaModel, list[str]]:
    mappings = CORE_MAPPINGS.copy()
    if domain_mappings:
        mappings.update(domain_mappings)
        
    unresolved = set()
    
    def expand_name(raw_name: str) -> str:
        parts = raw_name.replace("-", "_").split("_")
        expanded = []
        for p in parts:
            plower = p.lower()
            if plower in mappings:
                expanded.append(mappings[plower])
            else:
                # If it's short and not in mappings, it might be an unresolved abbreviation
                if len(plower) <= 4 and plower not in ("name", "type", "date", "time", "year", "code", "role", "user", "file", "path", "size", "hash", "salt", "key", "cert", "host", "port", "zone", "tier", "plan", "cost", "fee", "tax", "rate", "tag", "flag", "memo", "note", "link", "icon", "logo"):
                    unresolved.add(p)
                expanded.append(p.capitalize())
        return " ".join(expanded)
        
    for table in schema.tables:
        table.business_name = expand_name(table.name)
        for col in table.columns:
            col.business_name = expand_name(col.name)
            
    return schema, list(unresolved)

def apply_llm(schema: DatabaseSchemaModel, api_key: str, model: str) -> DatabaseSchemaModel:
    try:
        from openai import OpenAI
    except ImportError:
        import click
        click.secho("\n[ERROR] OpenAI SDK not installed. Run `pip install schemap-tool[enrich]` or remove the --enrich flag.", fg="red")
        import sys
        sys.exit(1)
        
    client = OpenAI(api_key=api_key)
    
    # We send a compressed version of the schema to save tokens and latency
    compressed_tables = []
    for t in schema.tables:
        compressed_tables.append({
            "name": t.name,
            "business_name_heuristic": t.business_name,
            "columns": [{"name": c.name, "heuristic": c.business_name} for c in t.columns]
        })
        
    prompt = f"""
    You are an expert Data Architect. 
    Review this database schema. Improve the heuristic business names for tables and columns to be professional and business-aware.
    Write a 1-sentence 'description' for each table explaining its business purpose.
    Generate 3 'common_journeys' (useful analytical queries a business user might run across these tables, e.g., 'Monthly Recurring Revenue by Customer Tier').
    
    Respond STRICTLY in JSON format:
    {{
        "tables": [
            {{
                "name": "raw_table_name",
                "business_name": "Perfect Business Name",
                "description": "...",
                "columns": [
                    {{"name": "raw_column_name", "business_name": "Perfect Business Name"}}
                ]
            }}
        ],
        "common_journeys": ["Query 1", "Query 2", "Query 3"]
    }}
    
    Schema:
    {json.dumps(compressed_tables)}
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Merge back into schema
    schema.common_journeys = result.get("common_journeys", schema.common_journeys)
    
    table_map = {t["name"]: t for t in result.get("tables", [])}
    for t in schema.tables:
        if t.name in table_map:
            t.business_name = table_map[t.name].get("business_name", t.business_name)
            t.description = table_map[t.name].get("description", t.description)
            col_map = {c["name"]: c for c in table_map[t.name].get("columns", [])}
            for c in t.columns:
                if c.name in col_map:
                    c.business_name = col_map[c.name].get("business_name", c.business_name)
                    
    return schema
