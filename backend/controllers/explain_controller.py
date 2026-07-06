from flask import jsonify, request

from models.user import User
from services.explain_service import ExplainService


class ExplainController:
    def __init__(self):
        self.explain_service = ExplainService()

    def run_explain(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        result = self.explain_service.run(user, workspace_id, data.get("sql", ""))

        if result["status"] == "error":
            return jsonify(result), 400

        return jsonify(result), 200
