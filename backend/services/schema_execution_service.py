from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.utils import create_server_engine, ensure_database_exists
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
from utils.schema_validators import find_table


def execute_schema(workspace_id: int, schema_data: dict, table_name: str | None = None) -> dict:
    if not can_execute_on_mysql():
        statements = (
            [build_table_sql(schema_data, table_name)]
            if table_name
            else build_schema_sql(schema_data)
        )
        return {
            **mysql_required_response("CREATE TABLE execution"),
            "statements": statements,
        }

    if table_name:
        tables = [find_table(schema_data, table_name)]
    else:
        tables = order_tables_for_creation(schema_data)

    database_url = get_workspace_database_url(workspace_id)
    ensure_database_exists(database_url)

    engine = create_server_engine(database_url)
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

    return {
        "executed": True,
        "database": get_workspace_database_name(workspace_id),
        "statements": executed,
    }
