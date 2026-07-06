from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from explain.database import get_connection_manager
from services.schema_sql_generator import (
    build_create_table_sql,
    build_schema_sql,
    build_table_sql,
    order_tables_for_creation,
)
from services.workspace_database import (
    can_execute_on_mysql,
    get_workspace_database_name,
    get_workspace_database_url,
)
from utils.mysql_features import mysql_required_response
from utils.schema_validators import empty_schema, find_table


def sync_workspace_schema_to_mysql(workspace_id: int, schema_data: dict | None) -> dict:
    """Materialize logical schema tables into the workspace MySQL database."""
    schema_data = schema_data or empty_schema()
    tables = schema_data.get("tables", [])
    if not tables:
        return {"synced": True, "tables_ensured": []}
    if not can_execute_on_mysql():
        return {"synced": False, "message": "MySQL is not configured.", "tables_ensured": []}

    get_connection_manager().ensure_workspace_database(workspace_id)
    from database.utils import create_server_engine

    engine = create_server_engine(get_workspace_database_url(workspace_id))
    ensured: list[str] = []
    try:
        with engine.begin() as connection:
            for table in order_tables_for_creation(schema_data):
                connection.execute(text(build_create_table_sql(table)))
                ensured.append(table["name"])
    except SQLAlchemyError as exc:
        return {
            "synced": False,
            "message": str(exc.__cause__ or exc),
            "tables_ensured": ensured,
            "database": get_workspace_database_name(workspace_id),
        }
    return {"synced": True, "tables_ensured": ensured, "database": get_workspace_database_name(workspace_id)}


def execute_schema(workspace_id: int, schema_data: dict, table_name: str | None = None) -> dict:
    if not can_execute_on_mysql():
        statements = (
            [build_table_sql(schema_data, table_name)] if table_name else build_schema_sql(schema_data)
        )
        return {**mysql_required_response("CREATE TABLE execution"), "statements": statements}

    if table_name:
        tables = [find_table(schema_data, table_name)]
    else:
        tables = order_tables_for_creation(schema_data)

    get_connection_manager().ensure_workspace_database(workspace_id)
    from database.utils import create_server_engine

    engine = create_server_engine(get_workspace_database_url(workspace_id))
    executed = []
    try:
        with engine.begin() as connection:
            for table in tables:
                sql = build_create_table_sql(table)
                connection.execute(text(sql))
                executed.append({
                    "table": table["name"],
                    "sql": sql,
                    "database": get_workspace_database_name(workspace_id),
                })
    except SQLAlchemyError as exc:
        return {
            "executed": False,
            "status": "error",
            "message": str(exc),
            "database": get_workspace_database_name(workspace_id),
            "statements": executed,
        }
    return {"executed": True, "database": get_workspace_database_name(workspace_id), "statements": executed}
