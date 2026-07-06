from flask import Flask, jsonify

from utils.exceptions import AppError


def register_error_handlers(app: Flask) -> None:
    """Register global JSON error handlers."""

    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        return jsonify({
            "error": exc.__class__.__name__,
            "message": exc.message,
        }), exc.status_code

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized", "message": str(error)}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden", "message": str(error)}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        message = getattr(error, "description", None) or "Internal server error"
        return jsonify({"error": "Internal server error", "message": message}), 500
