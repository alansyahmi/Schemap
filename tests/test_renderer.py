from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.renderer import render_markdown

def test_renderer_formats_markdown_correctly():
    """Verify that renderer.py correctly formats a Pydantic object into the target Markdown layout."""
    
    schema = DatabaseSchemaModel(
        tables=[
            TableModel(
                name="employees",
                description="Employee directory",
                columns=[
                    ColumnModel(
                        name="id",
                        data_type="integer",
                        is_nullable=False,
                        primary_key=True,
                        description="Employee ID"
                    ),
                    ColumnModel(
                        name="department_id",
                        data_type="integer",
                        is_nullable=True,
                        primary_key=False,
                        description=None
                    )
                ],
                foreign_keys=[
                    ForeignKeyModel(
                        column_name="department_id",
                        foreign_table_name="departments",
                        foreign_column_name="id"
                    )
                ]
            )
        ]
    )
    
    markdown = render_markdown(schema)
    
    assert "## Table: `employees`" in markdown
    assert "*Employee directory*" in markdown
    assert "- `id` (integer) **[PK]** *[NOT NULL]* - Employee ID" in markdown
    assert "- `department_id` (integer)" in markdown
    assert "- `department_id` -> `departments.id`" in markdown
