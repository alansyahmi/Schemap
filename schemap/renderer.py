import json
import yaml
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from .models import DatabaseSchemaModel

def _build_hierarchy_tree(table_name: str, table_map: dict, depth: int = 0, visited: set = None) -> list[str]:
    if visited is None:
        visited = set()
    if table_name in visited or depth > 3:
        return []
        
    visited.add(table_name)
    lines = []
    
    # Find tables that have foreign keys pointing TO table_name (children)
    children = []
    for t in table_map.values():
        if any(fk.foreign_table_name == table_name for fk in t.foreign_keys):
            children.append(t.name)
            
    for child in sorted(children):
        indent = "  " * depth + " └─ "
        lines.append(f"{indent}{child}")
        lines.extend(_build_hierarchy_tree(child, table_map, depth + 1, set(visited)))
        
    return lines

def _find_paths(start_table: str, table_map: dict, max_depth=3) -> list[list[str]]:
    paths = []
    queue = [[start_table]]
    while queue:
        path = queue.pop(0)
        if len(path) > max_depth:
            continue
        current = path[-1]
        
        children = [t.name for t in table_map.values() if any(fk.foreign_table_name == current for fk in t.foreign_keys)]
        is_leaf = True
        for child in children:
            if child not in path:
                is_leaf = False
                new_path = list(path)
                new_path.append(child)
                paths.append(new_path)
                queue.append(new_path)
                
    return paths

def enrich_schema_relationships(schema: DatabaseSchemaModel) -> DatabaseSchemaModel:
    table_map = {t.name: t for t in schema.tables}
    
    for t in schema.tables:
        tree_lines = [t.name] + _build_hierarchy_tree(t.name, table_map)
        if len(tree_lines) > 1:
            t.hierarchy_tree = "\n".join(tree_lines)
            
    # Find common journeys (paths of length >= 2)
    journeys = []
    # simple heuristic: look for roots (tables rarely referenced but having lots of refs to them)
    # Actually just look at common entities like users, customers, accounts
    roots = [t.name for t in schema.tables if "user" in t.name or "account" in t.name or "customer" in t.name or "tenant" in t.name]
    if not roots and schema.tables:
        roots = [schema.tables[0].name] # fallback
        
    for root in roots:
        paths = _find_paths(root, table_map)
        # Sort paths by length, keep top 3
        paths.sort(key=len, reverse=True)
        for p in paths[:3]:
            # Convert table names to title case for journey display
            journey_str = " → ".join(name.title().replace("_", "") for name in p)
            journeys.append(journey_str)
            
    schema.common_journeys = list(set(journeys))
    return schema

def render_output(schema: DatabaseSchemaModel, fmt: str = "markdown") -> str:
    """
    Renders the schema into the specified format string.
    """
    schema = enrich_schema_relationships(schema)
    
    if fmt == "json":
        return schema.model_dump_json(indent=2)
    elif fmt == "yaml":
        return yaml.dump(schema.model_dump(), sort_keys=False)
    elif fmt == "mcp":
        mcp_payload = {
            "mcpServers": {
                "schemap": {
                    "resources": [
                        {
                            "uri": "schema://database",
                            "name": "Database Schema Context",
                            "description": "Token-optimized representation of the database schema.",
                            "text": schema.model_dump_json(indent=2)
                        }
                    ]
                }
            }
        }
        return json.dumps(mcp_payload, indent=2)
    elif fmt == "xml":
        import xml.etree.ElementTree as ET
        root = ET.Element("DatabaseSchema")
        for t in schema.tables:
            te = ET.SubElement(root, "Table", name=t.name)
            if t.description:
                ET.SubElement(te, "Purpose").text = t.description
            cols = ET.SubElement(te, "Columns")
            for c in t.columns:
                ce = ET.SubElement(cols, "Column", name=c.name, type=c.data_type, pk=str(c.primary_key), nullable=str(c.is_nullable))
                if c.description:
                    ce.text = c.description
        from xml.dom import minidom
        return minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    else:
        # Default to markdown
        templates_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template("context.md.j2")
        return template.render(schema=schema)

def write_output(content: str, output_path: str) -> None:
    """
    Writes the rendered content to the specified file path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
