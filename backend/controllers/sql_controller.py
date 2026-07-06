from flask import jsonify, request

from models.user import User
from services.query_service import QueryService
from utils.request_helpers import clamp_limit


class SqlController:
    def __init__(self):
        self.query_service = QueryService()

    def execute(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        result = self.query_service.execute_sql(
            user,
            workspace_id,
            sql_text=data.get("sql", ""),
            save_query=bool(data.get("save_query", False)),
            title=data.get("title"),
        )
        status_code = 200 if result["execution"]["status"] in {"success", "skipped"} else 400
        return jsonify(result), status_code

    def execute_saved(self, user: User, workspace_id: int, query_id: int):
        result = self.query_service.execute_sql(
            user,
            workspace_id,
            sql_text="",
            query_id=query_id,
        )
        status_code = 200 if result["execution"]["status"] in {"success", "skipped"} else 400
        return jsonify(result), status_code

    def list_queries(self, user: User, workspace_id: int):
        queries = self.query_service.list_saved_queries(user, workspace_id)
        return jsonify({
            "queries": [query.to_dict() for query in queries],
            "total": len(queries),
        }), 200

    def save_query(self, user: User, workspace_id: int):
        data = request.get_json(silent=True) or {}
        query = self.query_service.save_query(
            user,
            workspace_id,
            title=data.get("title", ""),
            sql_text=data.get("sql", ""),
        )
        return jsonify({"query": query.to_dict()}), 201

    def get_query(self, user: User, workspace_id: int, query_id: int):
        query = self.query_service.get_saved_query(user, workspace_id, query_id)
        return jsonify({"query": query.to_dict()}), 200

    def delete_query(self, user: User, workspace_id: int, query_id: int):
        self.query_service.delete_saved_query(user, workspace_id, query_id)
        return jsonify({"message": "Query deleted successfully."}), 200

    def list_history(self, user: User, workspace_id: int):
        limit = clamp_limit(request.args.get("limit", default=50, type=int))
        runs = self.query_service.list_history(user, workspace_id, limit=limit)
        return jsonify({
            "runs": [run.to_dict() for run in runs],
            "total": len(runs),
        }), 200
