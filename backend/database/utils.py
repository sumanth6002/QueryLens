"""Database utility helpers."""

from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from utils.schema_validators import IDENTIFIER_PATTERN


def parse_mysql_url(database_url: str) -> tuple[str, str]:
    """
    Split a SQLAlchemy MySQL URL into (server_url, database_name).

    Example:
        mysql+pymysql://user:pass@localhost:3306/querylens
        -> ('mysql+pymysql://user:pass@localhost:3306', 'querylens')
    """
    parsed = urlparse(database_url)
    database_name = parsed.path.lstrip("/")

    if not database_name:
        raise ValueError("DATABASE_URL must include a database name.")

    server_url = database_url.rsplit("/", 1)[0]
    return server_url, database_name


def ensure_database_exists(database_url: str) -> None:
    """Create the MySQL database if it does not already exist."""
    if database_url.startswith("sqlite"):
        return

    server_url, database_name = parse_mysql_url(database_url)

    if not IDENTIFIER_PATTERN.match(database_name):
        raise ValueError(f"Invalid database name: {database_name}")

    engine = create_engine(
        server_url,
        isolation_level="AUTOCOMMIT",
    )

    with engine.connect() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )


def create_server_engine(database_url: str) -> Engine:
    """Return a SQLAlchemy engine bound to the configured database."""
    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    try:
        from flask import current_app

        engine_options = current_app.config.get("SQLALCHEMY_ENGINE_OPTIONS", engine_options)
    except RuntimeError:
        pass

    return create_engine(database_url, **engine_options)


def check_session_health() -> dict:
    """Run a lightweight query through the active Flask-SQLAlchemy session."""
    from database.connection import db

    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        db.session.rollback()
        return {"status": "error", "message": str(exc)}


def test_connection(database_url: str) -> dict:
    """
    Verify that the configured database is reachable.

    Returns a dict with status and diagnostic details.
    """
    try:
        engine = create_server_engine(database_url)
        with engine.connect() as connection:
            if database_url.startswith("sqlite"):
                connection.execute(text("SELECT 1"))
                return {
                    "status": "ok",
                    "database": database_url.rsplit("/", 1)[-1],
                    "engine": "sqlite",
                }

            result = connection.execute(text("SELECT DATABASE(), VERSION()"))
            row = result.one()

        return {
            "status": "ok",
            "database": row[0],
            "mysql_version": row[1],
            "engine": "mysql",
        }
    except SQLAlchemyError as exc:
        return {
            "status": "error",
            "message": str(exc.__cause__ or exc),
        }
