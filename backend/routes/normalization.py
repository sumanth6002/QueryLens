from flask import Blueprint

from controllers.normalization_controller import NormalizationController
from middleware.request_context import get_request_user

normalization_bp = Blueprint(
    "normalization",
    __name__,
    url_prefix="/api/workspaces/<int:workspace_id>/normalization",
)
controller = NormalizationController()


@normalization_bp.route("/analyze", methods=["POST"])
def analyze(workspace_id: int):
    return controller.analyze(get_request_user(), workspace_id)


@normalization_bp.route("/reports", methods=["GET"])
def list_reports(workspace_id: int):
    return controller.list_reports(get_request_user(), workspace_id)


@normalization_bp.route("/reports/<int:report_id>", methods=["GET"])
def get_report(workspace_id: int, report_id: int):
    return controller.get_report(get_request_user(), workspace_id, report_id)


@normalization_bp.route("/fd-sets", methods=["GET"])
def list_fd_sets(workspace_id: int):
    return controller.list_fd_sets(get_request_user(), workspace_id)


@normalization_bp.route("/fd-sets", methods=["POST"])
def save_fd_set(workspace_id: int):
    return controller.save_fd_set(get_request_user(), workspace_id)
