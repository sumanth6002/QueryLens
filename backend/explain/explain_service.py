"""EXPLAIN analysis service."""

from __future__ import annotations

import time

from explain.database import MySQLConnectionError, get_connection_manager
from explain.models import ExplainResult
from explain.parser import parse_explain_json, parse_explain_tabular
from models.user import User
from services.access_helpers import get_owned_workspace
from services.schema_execution_service import sync_workspace_schema_to_mysql
from utils.explain_validators import normalize_select_query


class ExplainService:
    def __init__(self) -> None:
        self._db = get_connection_manager()

    def run(self, user: User, workspace_id: int, sql: str) -> dict:
        workspace = get_owned_workspace(user, workspace_id)
        select_sql = normalize_select_query(sql)
        schema_data = workspace.schema_snapshot.schema_data if workspace.schema_snapshot else None
        sync_workspace_schema_to_mysql(workspace_id, schema_data)
        return self._execute_explain(workspace_id, select_sql).to_dict()

    def _execute_explain(self, workspace_id: int, select_sql: str) -> ExplainResult:
        database_name = self._db.get_workspace_database_name(workspace_id)
        start = time.perf_counter()
        if not self._db.is_configured:
            raise MySQLConnectionError(
                "MySQL is not configured. Set MYSQL_HOST, MYSQL_USER, and "
                "MYSQL_PASSWORD in backend/.env."
            )
        explain_payload, explain_format = self._db.run_explain(workspace_id, select_sql)
        if explain_format == "json":
            parsed = parse_explain_json(explain_payload)
            explain_json = explain_payload
        else:
            parsed = parse_explain_tabular(explain_payload)
            explain_json = None
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return ExplainResult(
            executed=True,
            status="success",
            message=None,
            execution_time_ms=elapsed_ms,
            query=select_sql,
            database=database_name,
            explain_format=explain_format,
            tree=parsed["tree"],
            table_nodes=parsed["table_nodes"],
            summary=parsed["summary"],
            issues=parsed["issues"],
            explain_json=explain_json,
        )
