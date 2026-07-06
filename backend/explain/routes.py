"""Flask routes for EXPLAIN analysis."""

from flask import Blueprint, jsonify, request

from explain.database import MySQLConnectionError, MySQLQueryError, get_connection_manager
from explain.explain_service import ExplainService
from middleware.request_context import get_request_user
from utils.exceptions import ValidationError

explain_bp = Blueprint("explain", __name__, url_prefix="/api/workspaces/<int:workspace_id>/explain")
_service = ExplainService()


@explain_bp.route("", methods=["POST"])
def run_explain(workspace_id: int):
    data = request.get_json(silent=True) or {}
    sql = data.get("sql", "")
    try:
        result = _service.run(get_request_user(), workspace_id, sql)
    except ValidationError as exc:
        return jsonify({"error": exc.__class__.__name__, "message": exc.message}), exc.status_code
    except MySQLConnectionError as exc:
        return jsonify({
            "executed": False, "status": "error", "message": str(exc),
            "query": sql, "database": get_connection_manager().get_workspace_database_name(workspace_id),
            "tree": None, "summary": None,
        }), 503
    except MySQLQueryError as exc:
        return jsonify({
            "executed": False, "status": "error", "message": str(exc),
            "query": sql, "database": get_connection_manager().get_workspace_database_name(workspace_id),
            "tree": None, "summary": None,
        }), 400
    status_code = 400 if result.get("status") == "error" else 200
    return jsonify(result), status_code
