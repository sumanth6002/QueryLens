from flask import Blueprint, jsonify

from database.utils import check_session_health

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Liveness probe — confirms the API is running."""
    return jsonify({
        "status": "ok",
        "service": "QueryLens API",
    }), 200


@health_bp.route("/api/health/db", methods=["GET"])
def database_health_check():
    """Readiness probe — confirms the API can reach the database."""
    result = check_session_health()

    status_code = 200 if result["status"] == "ok" else 503
    return jsonify(result), status_code
