from flask import Blueprint

from controllers.explain_controller import ExplainController
from middleware.request_context import get_request_user

explain_bp = Blueprint("explain", __name__, url_prefix="/api/workspaces/<int:workspace_id>/explain")
controller = ExplainController()


@explain_bp.route("", methods=["POST"])
def run_explain(workspace_id: int):
    return controller.run_explain(get_request_user(), workspace_id)
