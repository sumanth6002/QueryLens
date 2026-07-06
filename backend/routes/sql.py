from flask import Blueprint

from controllers.sql_controller import SqlController
from middleware.request_context import get_request_user

sql_bp = Blueprint("sql", __name__, url_prefix="/api/workspaces/<int:workspace_id>/sql")
controller = SqlController()


@sql_bp.route("/execute", methods=["POST"])
def execute_sql(workspace_id: int):
    return controller.execute(get_request_user(), workspace_id)


@sql_bp.route("/history", methods=["GET"])
def list_history(workspace_id: int):
    return controller.list_history(get_request_user(), workspace_id)


@sql_bp.route("/queries", methods=["GET"])
def list_queries(workspace_id: int):
    return controller.list_queries(get_request_user(), workspace_id)


@sql_bp.route("/queries", methods=["POST"])
def save_query(workspace_id: int):
    return controller.save_query(get_request_user(), workspace_id)


@sql_bp.route("/queries/<int:query_id>", methods=["GET"])
def get_query(workspace_id: int, query_id: int):
    return controller.get_query(get_request_user(), workspace_id, query_id)


@sql_bp.route("/queries/<int:query_id>", methods=["DELETE"])
def delete_query(workspace_id: int, query_id: int):
    return controller.delete_query(get_request_user(), workspace_id, query_id)


@sql_bp.route("/queries/<int:query_id>/execute", methods=["POST"])
def execute_saved_query(workspace_id: int, query_id: int):
    return controller.execute_saved(get_request_user(), workspace_id, query_id)
