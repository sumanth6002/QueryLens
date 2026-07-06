from flask import Blueprint

from controllers.workspace_controller import WorkspaceController

workspaces_bp = Blueprint("workspaces", __name__, url_prefix="/api/workspaces")
controller = WorkspaceController()


@workspaces_bp.route("/dashboard", methods=["GET"])
def dashboard():
    return controller.dashboard()


@workspaces_bp.route("", methods=["GET"])
def list_workspaces():
    return controller.list_workspaces()


@workspaces_bp.route("", methods=["POST"])
def create_workspace():
    return controller.create_workspace()


@workspaces_bp.route("/<int:workspace_id>", methods=["DELETE"])
def delete_workspace(workspace_id: int):
    return controller.delete_workspace(workspace_id)
