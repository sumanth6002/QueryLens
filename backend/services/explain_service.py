import json
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.utils import create_server_engine, ensure_database_exists
from models.user import User
from services.access_helpers import get_owned_workspace
from services.explain_parser import get_sample_explain_result, parse_explain_json
from services.workspace_database import (
    can_execute_on_mysql,
    get_workspace_database_name,
    get_workspace_database_url,
)
from utils.explain_validators import normalize_select_query
from utils.mysql_features import mysql_required_response


def explain_query(workspace_id: int, sql: str) -> dict:
    select_sql = normalize_select_query(sql)
    start = time.perf_counter()

    if not can_execute_on_mysql():
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        sample = get_sample_explain_result()

        return {
            **mysql_required_response(
                "EXPLAIN execution",
                execution_time_ms=elapsed_ms,
                query=select_sql,
                database=get_workspace_database_name(workspace_id),
            ),
            "message": "EXPLAIN execution requires a MySQL connection. Showing sample plan.",
            **sample,
        }

    database_url = get_workspace_database_url(workspace_id)
    ensure_database_exists(database_url)

    engine = create_server_engine(database_url)
    explain_sql = f"EXPLAIN FORMAT=JSON {select_sql}"

    try:
        with engine.connect() as connection:
            result = connection.execute(text(explain_sql))
            row = result.fetchone()

        if row is None:
            raise SQLAlchemyError("EXPLAIN returned no rows.")

        explain_json = json.loads(row[0])
        parsed = parse_explain_json(explain_json)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        return {
            "executed": True,
            "status": "success",
            "message": None,
            "execution_time_ms": elapsed_ms,
            "query": select_sql,
            "database": get_workspace_database_name(workspace_id),
            "explain_json": explain_json,
            **parsed,
        }
    except (SQLAlchemyError, json.JSONDecodeError, TypeError) as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "executed": False,
            "status": "error",
            "message": str(exc),
            "execution_time_ms": elapsed_ms,
            "query": select_sql,
            "database": get_workspace_database_name(workspace_id),
            "tree": None,
            "table_nodes": [],
            "summary": None,
        }


class ExplainService:
    """Run EXPLAIN analysis for a workspace-owned query."""

    def run(self, user: User, workspace_id: int, sql: str) -> dict:
        get_owned_workspace(user, workspace_id)
        return explain_query(workspace_id, sql)
