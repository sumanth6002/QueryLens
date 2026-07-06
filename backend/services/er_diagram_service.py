import re

from utils.schema_validators import empty_schema

MERMAID_SAFE_PATTERN = re.compile(r"[^a-zA-Z0-9_]")


def _sanitize_label(value: str) -> str:
    cleaned = MERMAID_SAFE_PATTERN.sub("_", value.strip())
    return cleaned or "relation"


def _format_column_type(data_type: str) -> str:
    return (
        data_type.replace("(", "_")
        .replace(")", "")
        .replace(",", "_")
        .replace(" ", "_")
    )


def _format_column_line(table_name: str, column: dict, primary_keys: set[str], foreign_keys: set[str]) -> str:
    markers = []

    if column["name"] in primary_keys:
        markers.append("PK")

    if column["name"] in foreign_keys:
        markers.append("FK")

    column_type = _format_column_type(column["data_type"])
    marker_suffix = f" {' '.join(markers)}" if markers else ""

    return f"        {column_type} {column['name']}{marker_suffix}"


def build_er_diagram(schema_data: dict | None) -> dict:
    """
    Convert workspace schema JSON into Mermaid erDiagram syntax.

    Returns metadata plus the diagram source string.
    """
    schema_data = schema_data or empty_schema()
    tables = schema_data.get("tables", [])

    if not tables:
        return {
            "empty": True,
            "mermaid": None,
            "message": "No tables defined in this workspace.",
            "table_count": 0,
            "relationship_count": 0,
            "tables": [],
            "relationships": [],
        }

    lines = ["erDiagram"]
    relationships = []

    for table in tables:
        table_name = table["name"]
        primary_keys = set(table.get("primary_key", []))
        foreign_key_columns = {
            column
            for foreign_key in table.get("foreign_keys", [])
            for column in foreign_key.get("columns", [])
        }

        lines.append(f"    {table_name} {{")
        for column in table["columns"]:
            lines.append(_format_column_line(table_name, column, primary_keys, foreign_key_columns))
        lines.append("    }")

    for table in tables:
        for foreign_key in table.get("foreign_keys", []):
            referenced_table = foreign_key["referenced_table"]
            label = foreign_key.get("name") or "_".join(foreign_key.get("columns", ["fk"]))
            safe_label = _sanitize_label(label)

            lines.append(
                f'    {table["name"]} }}o--|| {referenced_table} : "{safe_label}"'
            )
            relationships.append({
                "from_table": table["name"],
                "to_table": referenced_table,
                "columns": foreign_key.get("columns", []),
                "referenced_columns": foreign_key.get("referenced_columns", []),
                "label": safe_label,
            })

    return {
        "empty": False,
        "mermaid": "\n".join(lines),
        "message": None,
        "table_count": len(tables),
        "relationship_count": len(relationships),
        "tables": [table["name"] for table in tables],
        "relationships": relationships,
    }
