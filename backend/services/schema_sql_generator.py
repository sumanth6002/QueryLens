from utils.exceptions import ValidationError
from utils.schema_validators import find_table


def order_tables_for_creation(schema_data: dict) -> list[dict]:
    tables = schema_data.get("tables", [])
    table_map = {table["name"]: table for table in tables}
    visited: set[str] = set()
    ordered: list[dict] = []

    def visit(table_name: str) -> None:
        if table_name in visited:
            return

        if table_name not in table_map:
            raise ValidationError(f"Referenced table '{table_name}' is not defined.")

        visited.add(table_name)
        table = table_map[table_name]

        for foreign_key in table.get("foreign_keys", []):
            visit(foreign_key["referenced_table"])

        ordered.append(table)

    for table in tables:
        visit(table["name"])

    return ordered


def build_create_table_sql(table: dict) -> str:
    column_lines = []

    for column in table["columns"]:
        line = f"`{column['name']}` {column['data_type']}"

        if not column.get("nullable", True):
            line += " NOT NULL"

        if column.get("auto_increment"):
            line += " AUTO_INCREMENT"

        column_lines.append(line)

    if table.get("primary_key"):
        pk_columns = ", ".join(f"`{column}`" for column in table["primary_key"])
        column_lines.append(f"PRIMARY KEY ({pk_columns})")

    for foreign_key in table.get("foreign_keys", []):
        local_columns = ", ".join(f"`{column}`" for column in foreign_key["columns"])
        referenced_columns = ", ".join(
            f"`{column}`" for column in foreign_key["referenced_columns"]
        )
        constraint_name = foreign_key.get("name") or (
            f"fk_{table['name']}_{'_'.join(foreign_key['columns'])}"
        )
        line = (
            f"CONSTRAINT `{constraint_name}` FOREIGN KEY ({local_columns}) "
            f"REFERENCES `{foreign_key['referenced_table']}` ({referenced_columns}) "
            f"ON DELETE {foreign_key['on_delete']}"
        )
        column_lines.append(line)

    columns_sql = ",\n  ".join(column_lines)
    return f"CREATE TABLE IF NOT EXISTS `{table['name']}` (\n  {columns_sql}\n);"


def build_schema_sql(schema_data: dict) -> list[dict]:
    statements = []

    for table in order_tables_for_creation(schema_data):
        statements.append({
            "table": table["name"],
            "sql": build_create_table_sql(table),
        })

    return statements


def build_table_sql(schema_data: dict, table_name: str) -> dict:
    table = find_table(schema_data, table_name)
    return {
        "table": table["name"],
        "sql": build_create_table_sql(table),
    }
