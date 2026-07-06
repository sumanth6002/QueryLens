from flask import current_app

from database.utils import parse_mysql_url


def get_workspace_database_name(workspace_id: int) -> str:
    return f"querylens_ws_{workspace_id}"


def get_workspace_database_url(workspace_id: int) -> str:
    base_url = current_app.config["SQLALCHEMY_DATABASE_URI"]
    server_url, _ = parse_mysql_url(base_url)
    database_name = get_workspace_database_name(workspace_id)
    return f"{server_url}/{database_name}"


def can_execute_on_mysql() -> bool:
    database_url = current_app.config["SQLALCHEMY_DATABASE_URI"]
    return database_url.startswith("mysql")
