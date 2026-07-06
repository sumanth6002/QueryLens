from flask import Blueprint

from controllers.index_advisor_controller import IndexAdvisorController
from middleware.request_context import get_request_user

index_advisor_bp = Blueprint(
    "index_advisor",
    __name__,
    url_prefix="/api/workspaces/<int:workspace_id>/index-advisor",
)
controller = IndexAdvisorController()


@index_advisor_bp.route("/analyze", methods=["POST"])
def analyze(workspace_id: int):
    return controller.analyze(get_request_user(), workspace_id)


@index_advisor_bp.route("/recommendations", methods=["GET"])
def list_recommendations(workspace_id: int):
    return controller.list_recommendations(get_request_user(), workspace_id)


@index_advisor_bp.route("/recommendations/<int:recommendation_id>", methods=["GET"])
def get_recommendation(workspace_id: int, recommendation_id: int):
    return controller.get_recommendation(get_request_user(), workspace_id, recommendation_id)
