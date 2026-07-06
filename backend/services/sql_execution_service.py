import time

from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.utils import create_server_engine, ensure_database_exists
from services.workspace_database import (
    can_execute_on_mysql,
    get_workspace_database_name,
    get_workspace_database_url,
)
from utils.mysql_features import mysql_required_response
from utils.sql_safety import get_statement_type, parse_and_validate_sql


def _max_result_rows() -> int:
    return int(current_app.config.get("SQL_MAX_RESULT_ROWS", 500))


def _serialize_row(row) -> list:
    return [value.isoformat() if hasattr(value, "isoformat") else value for value in row]


def _execute_statement(connection, statement: str) -> dict:
    statement_type = get_statement_type(statement)
    result = connection.execute(text(statement))

    if statement_type == "SELECT" or statement_type in {"SHOW", "DESCRIBE", "EXPLAIN"}:
        rows = result.fetchmany(_max_result_rows() + 1)
        truncated = len(rows) > _max_result_rows()

        if truncated:
            rows = rows[:_max_result_rows()]

        columns = list(result.keys()) if result.keys() else []
        serialized_rows = [_serialize_row(row) for row in rows]

        return {
            "statement_type": statement_type,
            "status": "success",
            "row_count": len(serialized_rows),
            "columns": columns,
            "rows": serialized_rows,
            "truncated": truncated,
        }

    return {
        "statement_type": statement_type,
        "status": "success",
        "row_count": result.rowcount,
        "columns": [],
        "rows": [],
        "truncated": False,
    }


def execute_sql(workspace_id: int, sql: str) -> dict:
    statements = parse_and_validate_sql(sql)
    start = time.perf_counter()

    if not can_execute_on_mysql():
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            **mysql_required_response("SQL execution"),
            "execution_time_ms": elapsed_ms,
            "statements": statements,
            "results": [],
            "row_count": 0,
            "result_columns": [],
            "result_preview": [],
            "error_message": None,
        }

    database_url = get_workspace_database_url(workspace_id)
    ensure_database_exists(database_url)

    engine = create_server_engine(database_url)
    results = []
    total_row_count = 0
    status = "success"
    error_message = None

    try:
        with engine.begin() as connection:
            for index, statement in enumerate(statements):
                statement_result = _execute_statement(connection, statement)
                statement_result["statement_index"] = index
                results.append(statement_result)
                total_row_count += statement_result.get("row_count") or 0
    except SQLAlchemyError as exc:
        status = "error"
        error_message = str(exc.__cause__ or exc)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    last_result = results[-1] if results else {}

    return {
        "executed": status == "success",
        "database": get_workspace_database_name(workspace_id),
        "status": status,
        "execution_time_ms": elapsed_ms,
        "row_count": total_row_count,
        "result_columns": last_result.get("columns", []),
        "result_preview": last_result.get("rows", []),
        "results": results,
        "error_message": error_message,
        "statements": statements,
    }
