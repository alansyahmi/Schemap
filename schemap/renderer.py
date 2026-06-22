from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from .models import DatabaseSchemaModel

def render_markdown(schema: DatabaseSchemaModel, template_name: str = "context.md.j2") -> str:
    """
    Renders the validated schema into a markdown string using Jinja2.
    """
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template(template_name)
    
    return template.render(schema=schema)

def write_markdown(markdown_content: str, output_path: str) -> None:
    """
    Writes the rendered markdown to the specified file path.
    """
    path = Path(output_path)
    # Create directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
