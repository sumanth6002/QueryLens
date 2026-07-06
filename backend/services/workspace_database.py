"""Workspace-scoped MySQL database URL helpers."""

from explain.database import get_connection_manager


def get_workspace_database_name(workspace_id: int) -> str:
    return get_connection_manager().get_workspace_database_name(workspace_id)


def get_workspace_database_url(workspace_id: int) -> str:
    manager = get_connection_manager()
    if manager.is_configured:
        return manager.get_workspace_database_url(workspace_id)

    from flask import current_app
    from database.utils import parse_mysql_url

    base_url = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not base_url.startswith("mysql"):
        raise RuntimeError("MySQL is not configured for workspace execution.")
    server_url, _ = parse_mysql_url(base_url)
    return f"{server_url}/{get_workspace_database_name(workspace_id)}"


def can_execute_on_mysql() -> bool:
    if get_connection_manager().is_configured:
        return True
    try:
        from flask import current_app
        return current_app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql")
    except RuntimeError:
        return False
