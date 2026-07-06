"""Flask blueprint registration."""

from flask import Flask

from routes.auth import auth_bp
from routes.explain import explain_bp
from routes.health import health_bp
from routes.index_advisor import index_advisor_bp
from routes.normalization import normalization_bp
from routes.schema import schema_bp
from routes.sql import sql_bp
from routes.workspaces import workspaces_bp


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(workspaces_bp)
    app.register_blueprint(schema_bp)
    app.register_blueprint(sql_bp)
    app.register_blueprint(explain_bp)
    app.register_blueprint(normalization_bp)
    app.register_blueprint(index_advisor_bp)
