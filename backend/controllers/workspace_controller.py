from flask import jsonify, request

from middleware.request_context import get_request_user
from services.workspace_service import WorkspaceService


class WorkspaceController:
    def __init__(self):
        self.workspace_service = WorkspaceService()

    def dashboard(self):
        result = self.workspace_service.get_dashboard(get_request_user())
        return jsonify(result), 200

    def list_workspaces(self):
        workspaces = self.workspace_service.list_workspaces(get_request_user())
        return jsonify({
            "workspaces": [workspace.to_dict() for workspace in workspaces],
            "total": len(workspaces),
        }), 200

    def create_workspace(self):
        data = request.get_json(silent=True) or {}
        workspace = self.workspace_service.create_workspace(
            user=get_request_user(),
            name=data.get("name", ""),
            description=data.get("description"),
        )
        return jsonify({"workspace": workspace.to_dict()}), 201

    def delete_workspace(self, workspace_id: int):
        self.workspace_service.delete_workspace(get_request_user(), workspace_id)
        return jsonify({"message": "Workspace deleted successfully."}), 200
