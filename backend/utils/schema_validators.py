import re

from utils.exceptions import ConflictError, NotFoundError, ValidationError

IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")
ALLOWED_TYPES = {
    "INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT",
    "VARCHAR", "CHAR", "TEXT",
    "BOOLEAN", "BOOL",
    "DATE", "DATETIME", "TIMESTAMP",
    "DECIMAL", "FLOAT", "DOUBLE",
}
TYPE_WITH_LENGTH = re.compile(
    r"^(VARCHAR|CHAR|DECIMAL)\((\d+)(?:,\s*(\d+))?\)$",
    re.IGNORECASE,
)


def empty_schema() -> dict:
    return {"tables": []}


def validate_identifier(name: str, label: str) -> str:
    cleaned = (name or "").strip()

    if not cleaned or not IDENTIFIER_PATTERN.match(cleaned):
        raise ValidationError(
            f"{label} must start with a letter or underscore and contain only "
            "letters, numbers, or underscores (max 64 characters)."
        )

    return cleaned


def validate_data_type(data_type: str) -> str:
    cleaned = (data_type or "").strip().upper()

    if not cleaned:
        raise ValidationError("Column data type is required.")

    if cleaned in ALLOWED_TYPES:
        return cleaned

    match = TYPE_WITH_LENGTH.match(cleaned)
    if match:
        base_type = match.group(1).upper()
        if base_type not in ALLOWED_TYPES:
            raise ValidationError(f"Unsupported data type: {data_type}")
        return cleaned

    raise ValidationError(
        f"Unsupported data type: {data_type}. "
        f"Allowed types: {', '.join(sorted(ALLOWED_TYPES))} and sized variants like VARCHAR(255)."
    )


def validate_column(column: dict) -> dict:
    if not isinstance(column, dict):
        raise ValidationError("Each column must be an object.")

    name = validate_identifier(column.get("name", ""), "Column name")
    data_type = validate_data_type(column.get("data_type", ""))

    return {
        "name": name,
        "data_type": data_type,
        "nullable": bool(column.get("nullable", True)),
        "auto_increment": bool(column.get("auto_increment", False)),
    }


def validate_foreign_key(
    foreign_key: dict,
    table_names: set[str],
    table_map: dict[str, dict] | None = None,
) -> dict:
    if not isinstance(foreign_key, dict):
        raise ValidationError("Each foreign key must be an object.")

    columns = foreign_key.get("columns", [])
    referenced_table = validate_identifier(
        foreign_key.get("referenced_table", ""),
        "Referenced table",
    )
    referenced_columns = foreign_key.get("referenced_columns", [])

    if not columns:
        raise ValidationError("Foreign key must reference at least one column.")

    if referenced_table not in table_names:
        raise ValidationError(f"Referenced table '{referenced_table}' does not exist in the schema.")

    if not referenced_columns:
        raise ValidationError("Foreign key must reference at least one column in the parent table.")

    cleaned_columns = [validate_identifier(column, "Foreign key column") for column in columns]
    cleaned_referenced_columns = [
        validate_identifier(column, "Referenced column") for column in referenced_columns
    ]

    if len(cleaned_columns) != len(cleaned_referenced_columns):
        raise ValidationError("Foreign key column counts must match referenced column counts.")

    if table_map and referenced_table in table_map:
        parent_columns = {
            column["name"] for column in table_map[referenced_table].get("columns", [])
        }
        missing_parent = [
            column for column in cleaned_referenced_columns if column not in parent_columns
        ]
        if missing_parent:
            raise ValidationError(
                f"Referenced columns not found on table '{referenced_table}': "
                f"{', '.join(missing_parent)}"
            )

    on_delete = (foreign_key.get("on_delete") or "RESTRICT").upper()
    if on_delete not in {"RESTRICT", "CASCADE", "SET NULL", "NO ACTION"}:
        raise ValidationError("on_delete must be RESTRICT, CASCADE, SET NULL, or NO ACTION.")

    fk_name = foreign_key.get("name")
    if fk_name:
        fk_name = validate_identifier(fk_name, "Foreign key name")

    return {
        "name": fk_name,
        "columns": cleaned_columns,
        "referenced_table": referenced_table,
        "referenced_columns": cleaned_referenced_columns,
        "on_delete": on_delete,
    }


def validate_table_payload(
    payload: dict,
    *,
    existing_table_names: set[str] | None = None,
    current_name: str | None = None,
    schema_tables: list[dict] | None = None,
) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("Table payload must be an object.")

    existing_table_names = existing_table_names or set()
    name = validate_identifier(payload.get("name", current_name or ""), "Table name")

    if current_name is None and name in existing_table_names:
        raise ConflictError(f"Table '{name}' already exists.")
    if current_name and name != current_name and name in existing_table_names:
        raise ConflictError(f"Table '{name}' already exists.")

    columns = payload.get("columns", [])
    if not columns:
        raise ValidationError("A table must have at least one column.")

    validated_columns = [validate_column(column) for column in columns]
    column_names = [column["name"] for column in validated_columns]
    if len(column_names) != len(set(column_names)):
        raise ValidationError("Duplicate column names are not allowed in a table.")

    column_name_set = set(column_names)

    primary_key = payload.get("primary_key", [])
    if primary_key:
        primary_key = [validate_identifier(column, "Primary key column") for column in primary_key]
        missing = [column for column in primary_key if column not in column_name_set]
        if missing:
            raise ValidationError(f"Primary key columns not found: {', '.join(missing)}")

    table_names_for_fk = set(existing_table_names)
    table_names_for_fk.add(name)

    table_map = {table["name"]: table for table in (schema_tables or [])}

    foreign_keys = [
        validate_foreign_key(foreign_key, table_names_for_fk, table_map or None)
        for foreign_key in payload.get("foreign_keys", [])
    ]

    for foreign_key in foreign_keys:
        missing = [column for column in foreign_key["columns"] if column not in column_names]
        if missing:
            raise ValidationError(
                f"Foreign key columns not found in table '{name}': {', '.join(missing)}"
            )

    return {
        "name": name,
        "columns": validated_columns,
        "primary_key": primary_key,
        "foreign_keys": foreign_keys,
    }


def find_table(schema_data: dict, table_name: str) -> dict:
    for table in schema_data.get("tables", []):
        if table["name"] == table_name:
            return table

    raise NotFoundError(f"Table '{table_name}' not found.")
