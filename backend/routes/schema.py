from flask import Blueprint

from controllers.schema_controller import SchemaController
from middleware.request_context import get_request_user

schema_bp = Blueprint("schema", __name__, url_prefix="/api/workspaces/<int:workspace_id>/schema")
controller = SchemaController()


@schema_bp.route("", methods=["GET"])
def get_schema(workspace_id: int):
    return controller.get_schema(get_request_user(), workspace_id)


@schema_bp.route("/tables", methods=["POST"])
def create_table(workspace_id: int):
    return controller.create_table(get_request_user(), workspace_id)


@schema_bp.route("/tables/<string:table_name>", methods=["PUT"])
def update_table(workspace_id: int, table_name: str):
    return controller.update_table(get_request_user(), workspace_id, table_name)


@schema_bp.route("/tables/<string:table_name>", methods=["DELETE"])
def delete_table(workspace_id: int, table_name: str):
    return controller.delete_table(get_request_user(), workspace_id, table_name)


@schema_bp.route("/sql", methods=["GET"])
def preview_sql(workspace_id: int):
    return controller.preview_sql(get_request_user(), workspace_id)


@schema_bp.route("/execute", methods=["POST"])
def execute_schema(workspace_id: int):
    return controller.execute_schema(get_request_user(), workspace_id)


@schema_bp.route("/er-diagram", methods=["GET"])
def get_er_diagram(workspace_id: int):
    return controller.get_er_diagram(get_request_user(), workspace_id)
