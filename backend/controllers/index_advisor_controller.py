from flask import jsonify, request

from models.user import User
from services.index_advisor_service import IndexAdvisorService
from utils.request_helpers import clamp_limit


class IndexAdvisorController:
    def __init__(self):
        self.index_advisor_service = IndexAdvisorService()

    def analyze(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        result = self.index_advisor_service.analyze(
            user,
            workspace_id,
            data.get("sql", ""),
            save=bool(data.get("save", False)),
        )
        return jsonify(result), 200

    def list_recommendations(self, user: User, workspace_id: int):
        limit = clamp_limit(
            request.args.get("limit", default=20, type=int),
            default=20,
        )
        records = self.index_advisor_service.list_recommendations(user, workspace_id, limit=limit)
        return jsonify({
            "recommendations": [record.to_dict() for record in records],
            "total": len(records),
        }), 200

    def get_recommendation(self, user: User, workspace_id: int, recommendation_id: int):
        record = self.index_advisor_service.get_recommendation(user, workspace_id, recommendation_id)
        return jsonify({"recommendation": record.to_dict()}), 200
