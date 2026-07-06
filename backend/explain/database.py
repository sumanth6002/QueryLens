"""MySQL connection manager for EXPLAIN and workspace query execution."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from database.utils import ensure_database_exists, parse_mysql_url
from utils.schema_validators import IDENTIFIER_PATTERN

MYSQL_ERROR_TABLE_NOT_FOUND = 1146
MYSQL_ERROR_SYNTAX = 1064
MYSQL_ERROR_UNKNOWN_DATABASE = 1049
MYSQL_ERROR_ACCESS_DENIED = 1045
MYSQL_ERROR_CONNECTION = 2003


class MySQLConnectionError(Exception):
    """Raised when MySQL is misconfigured or unreachable."""


class MySQLQueryError(Exception):
    """Raised when EXPLAIN fails due to SQL or schema issues."""


def _extract_mysql_error_code(exc: Exception) -> int | None:
    orig = getattr(exc, "orig", None)
    if orig is not None and getattr(orig, "args", None):
        try:
            return int(orig.args[0])
        except (TypeError, ValueError):
            return None
    return None


def humanize_mysql_error(exc: Exception) -> str:
    code = _extract_mysql_error_code(exc)
    message = str(getattr(exc, "orig", None) or exc)

    if code == MYSQL_ERROR_TABLE_NOT_FOUND or "doesn't exist" in message.lower():
        match = re.search(r"Table '([^']+)' doesn't exist", message)
        table_ref = match.group(1) if match else "requested table"
        return (
            f"Table does not exist in the workspace MySQL database: {table_ref}. "
            "Define the table in Schema Builder (same workspace) or check the name "
            "in your SELECT query."
        )

    if code == MYSQL_ERROR_SYNTAX or "syntax" in message.lower():
        return f"SQL syntax error: {message}"

    if code == MYSQL_ERROR_UNKNOWN_DATABASE:
        return f"Database not found: {message}"

    if code in {MYSQL_ERROR_ACCESS_DENIED, MYSQL_ERROR_CONNECTION} or "Can't connect" in message:
        return f"Database connection failed: {message}"

    return message


class MySQLConnectionManager:
    """SQLAlchemy engine factory for per-workspace MySQL databases."""

    ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    def __init__(self) -> None:
        self._server_url = self._resolve_server_url()

    @property
    def is_configured(self) -> bool:
        return bool(self._server_url)

    def _resolve_server_url(self) -> str | None:
        explicit_url = os.environ.get("MYSQL_URL", "").strip()
        if explicit_url:
            if not explicit_url.startswith("mysql"):
                raise MySQLConnectionError("MYSQL_URL must use mysql+pymysql://")
            if "/" in explicit_url.rsplit("@", 1)[-1]:
                server_url, _ = parse_mysql_url(explicit_url)
            else:
                server_url = explicit_url.rstrip("/")
            return server_url

        host = os.environ.get("MYSQL_HOST", "").strip()
        if not host:
            database_url = os.environ.get("DATABASE_URL", "").strip()
            if database_url.startswith("mysql"):
                server_url, _ = parse_mysql_url(database_url)
                return server_url
            return None

        user = os.environ.get("MYSQL_USER", "root")
        password = os.environ.get("MYSQL_PASSWORD", "")
        port = os.environ.get("MYSQL_PORT", "3306")
        return (
            f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
            f"@{host}:{port}"
        )

    def get_workspace_database_name(self, workspace_id: int) -> str:
        return f"querylens_ws_{workspace_id}"

    def get_workspace_database_url(self, workspace_id: int) -> str:
        if not self.is_configured:
            raise MySQLConnectionError(
                "MySQL is not configured. Set MYSQL_HOST, MYSQL_USER, and "
                "MYSQL_PASSWORD (or MYSQL_URL) in backend/.env."
            )
        database_name = self.get_workspace_database_name(workspace_id)
        if not IDENTIFIER_PATTERN.match(database_name):
            raise MySQLConnectionError(f"Invalid workspace database name: {database_name}")
        return f"{self._server_url}/{database_name}"

    def create_engine(self, database_url: str | None = None, *, workspace_id: int | None = None) -> Engine:
        if database_url is None:
            if workspace_id is None:
                raise ValueError("database_url or workspace_id required")
            database_url = self.get_workspace_database_url(workspace_id)
        return create_engine(database_url, **self.ENGINE_OPTIONS)

    def ensure_workspace_database(self, workspace_id: int) -> None:
        ensure_database_exists(self.get_workspace_database_url(workspace_id))

    def test_connection(self) -> dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "error",
                "message": "MySQL is not configured. Set MYSQL_* variables in backend/.env.",
            }
        try:
            engine = create_engine(self._server_url, **self.ENGINE_OPTIONS)
            with engine.connect() as connection:
                version = connection.execute(text("SELECT VERSION()")).one()[0]
            return {"status": "ok", "mysql_version": version, "engine": "mysql"}
        except SQLAlchemyError as exc:
            return {"status": "error", "message": humanize_mysql_error(exc)}

    def supports_json_explain(self, connection) -> bool:
        try:
            version = str(connection.execute(text("SELECT VERSION()")).one()[0])
        except SQLAlchemyError:
            return False
        match = re.match(r"^(\d+)\.(\d+)", version)
        if not match:
            return False
        major, minor = int(match.group(1)), int(match.group(2))
        return major > 5 or (major == 5 and minor >= 6)

    def run_explain(self, workspace_id: int, select_sql: str) -> tuple[Any, str]:
        self.ensure_workspace_database(workspace_id)
        engine = self.create_engine(workspace_id=workspace_id)
        try:
            with engine.connect() as connection:
                if self.supports_json_explain(connection):
                    row = connection.execute(text(f"EXPLAIN FORMAT=JSON {select_sql}")).fetchone()
                    if row is None:
                        raise MySQLQueryError("EXPLAIN returned no rows.")
                    return json.loads(row[0]), "json"

                result = connection.execute(text(f"EXPLAIN {select_sql}"))
                rows = [dict(row._mapping) for row in result]
                if not rows:
                    raise MySQLQueryError("EXPLAIN returned no rows.")
                return rows, "tabular"
        except (json.JSONDecodeError, TypeError) as exc:
            raise MySQLQueryError(f"Failed to parse EXPLAIN output: {exc}") from exc
        except SQLAlchemyError as exc:
            message = humanize_mysql_error(exc)
            code = _extract_mysql_error_code(exc)
            if (
                code in {MYSQL_ERROR_ACCESS_DENIED, MYSQL_ERROR_CONNECTION}
                or "connection failed" in message.lower()
            ):
                raise MySQLConnectionError(message) from exc
            raise MySQLQueryError(message) from exc


@lru_cache(maxsize=1)
def get_connection_manager() -> MySQLConnectionManager:
    return MySQLConnectionManager()
